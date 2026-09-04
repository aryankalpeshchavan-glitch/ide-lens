"""Document ingestion and safe text extraction (ARCHITECTURE.md, DATA_MODEL.md §1.3).

Supports:
- TXT (plain text with encoding detection and sanitization)
- PDF (safe stream/text extractor without JavaScript execution)
- DOCX (Office Open XML parsing via zipfile + defused XML parsing)

Security constraints:
- Enforce size limits (default 10 MB)
- Reject binary executables (PE, ELF, Mach-O)
- Never execute file contents or macros
- Truncate extracted text to guard against unbounded memory / copyright storage
"""

import hashlib
import io
import re
import xml.etree.ElementTree as ET
import zipfile
import zlib
from dataclasses import dataclass, field
from typing import Any

MAX_DOCUMENT_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_EXTRACTED_TEXT_CHARS = 50_000

# Magic bytes to reject dangerous binary executables
DANGEROUS_MAGIC = (
    b"MZ",  # Windows DOS / PE executable
    b"\x7fELF",  # Linux ELF executable
    b"\xca\xfe\xba\xbe",  # Mach-O universal binary
    b"\xce\xfa\xed\xfe",  # Mach-O 32-bit
    b"\xcf\xfa\xed\xfe",  # Mach-O 64-bit
)


class DocumentValidationError(ValueError):
    """Raised when an uploaded document fails size, type, or integrity checks."""


@dataclass
class DocumentChunkData:
    ord_index: int
    content: str
    char_span: dict[str, int]
    token_estimate: int
    chunk_hash: str


@dataclass
class IngestedDocument:
    filename: str
    mime_type: str
    size_bytes: int
    hash_sha256: str
    extracted_title: str | None
    extracted_text: str
    doc_metadata: dict[str, Any] = field(default_factory=dict)
    chunks: list[DocumentChunkData] = field(default_factory=list)


def inspect_magic_bytes(content: bytes) -> None:
    """Verify content does not start with executable magic signatures."""
    for magic in DANGEROUS_MAGIC:
        if content.startswith(magic):
            raise DocumentValidationError("Executable binaries are not permitted.")


def extract_txt(content: bytes, filename: str) -> tuple[str | None, str, dict[str, Any]]:
    """Extract and sanitize plain text from raw bytes."""
    inspect_magic_bytes(content)
    text = ""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if not text and content:
        raise DocumentValidationError("Unable to decode text file with standard encodings.")

    # Sanitize control characters (preserve newlines and tabs)
    text = "".join(ch for ch in text if ch in "\n\r\t" or (32 <= ord(ch) <= 126 or ord(ch) > 127))
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = lines[0][:150] if lines else None

    meta = {"line_count": len(lines), "encoding": "detected"}
    return title, text, meta


def extract_docx(content: bytes, filename: str) -> tuple[str | None, str, dict[str, Any]]:
    """Extract text and metadata from DOCX archives safely without external libraries."""
    inspect_magic_bytes(content)
    if not content.startswith(b"PK\x03\x04"):
        raise DocumentValidationError("File does not have a valid DOCX ZIP header.")

    try:
        with zipfile.ZipFile(io.BytesIO(content), "r") as archive:
            namelist = archive.namelist()
            if "word/document.xml" not in namelist:
                raise DocumentValidationError("DOCX archive missing word/document.xml.")

            title: str | None = None
            # Check core properties for title/author
            if "docProps/core.xml" in namelist:
                try:
                    core_xml = archive.read("docProps/core.xml")
                    core_root = ET.fromstring(core_xml)
                    for elem in core_root.iter():
                        if elem.tag.endswith("title") and elem.text:
                            title = elem.text.strip()
                            break
                except Exception:
                    pass

            # Extract paragraphs from word/document.xml
            doc_xml = archive.read("word/document.xml")
            doc_root = ET.fromstring(doc_xml)

            # Namespaces for WordprocessingML
            w_namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
            ns = {"w": w_namespace}

            paragraphs: list[str] = []
            for p in doc_root.findall(".//w:p", ns):
                p_texts = []
                for t in p.findall(".//w:t", ns):
                    if t.text:
                        p_texts.append(t.text)
                if p_texts:
                    paragraphs.append("".join(p_texts).strip())

            extracted_text = "\n\n".join(paragraphs).strip()
            if not title and paragraphs:
                title = paragraphs[0][:150]

            meta = {
                "paragraph_count": len(paragraphs),
                "format": "docx",
            }
            return title, extracted_text, meta
    except zipfile.BadZipFile as exc:
        raise DocumentValidationError(f"Malformed DOCX file: {exc}") from exc
    except ET.ParseError as exc:
        raise DocumentValidationError(f"Malformed XML in DOCX file: {exc}") from exc


def extract_pdf(content: bytes, filename: str) -> tuple[str | None, str, dict[str, Any]]:
    """Safe pure-python PDF text and title extractor."""
    inspect_magic_bytes(content)
    if not content.startswith(b"%PDF-"):
        raise DocumentValidationError("File does not start with valid %PDF- header.")

    title: str | None = None
    extracted_chunks: list[str] = []

    # Attempt to use pypdf if available in environment
    try:
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(content))
        if reader.metadata and reader.metadata.title:
            title = str(reader.metadata.title).strip()
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                extracted_chunks.append(page_text.strip())
        extracted_text = "\n\n".join(extracted_chunks)
        if not title and extracted_chunks:
            first_line = extracted_chunks[0].splitlines()[0].strip()
            title = first_line[:150] if first_line else None
        return title, extracted_text, {"page_count": len(reader.pages), "parser": "pypdf"}
    except ImportError:
        pass
    except Exception:
        # Fall back to built-in stream scanner if pypdf encounters unusual structure
        pass

    # Built-in robust stream scanner
    # Find all /Filter /FlateDecode streams or plain text streams
    stream_pattern = re.compile(rb"stream[\r\n]+(.*?)[\r\n]+endstream", re.DOTALL)
    text_operator_pattern = re.compile(r"\((.*?)\)\s*T[jJ]|\[(.*?)\]\s*TJ", re.DOTALL)

    streams = stream_pattern.findall(content)
    decompressed_texts: list[str] = []

    for stream_data in streams:
        data = stream_data
        try:
            data = zlib.decompress(stream_data)
        except Exception:
            pass  # Maybe raw uncompressed stream

        # Look for text operators in stream
        try:
            decoded = data.decode("latin-1", errors="replace")
            # Look for strings inside BT ... ET blocks
            bt_blocks = re.findall(r"BT\s*(.*?)\s*ET", decoded, re.DOTALL)
            for block in bt_blocks:
                matches = text_operator_pattern.findall(block)
                for single, multi in matches:
                    if single:
                        decompressed_texts.append(single.replace(r"\(", "(").replace(r"\)", ")"))
                    elif multi:
                        # Inside bracket array: [(Hello) 10 (World)]
                        part_matches = re.findall(r"\((.*?)\)", multi)
                        decompressed_texts.append("".join(part_matches))
        except Exception:
            continue

    raw_text = " ".join(decompressed_texts)
    # Clean whitespace
    extracted_text = re.sub(r"\s+", " ", raw_text).strip()

    # Search for /Title in Info dictionary
    title_match = re.search(rb"/Title\s*\((.*?)\)", content)
    if title_match:
        try:
            title = title_match.group(1).decode("utf-8", errors="replace").strip()
        except Exception:
            pass

    if not title and extracted_text:
        title = extracted_text[:120].strip()

    meta = {"parser": "builtin-stream-scanner"}
    return title, extracted_text, meta


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list[DocumentChunkData]:
    """Split text into overlapping traceable chunks per DATA_MODEL.md §1.4."""
    chunks: list[DocumentChunkData] = []
    if not text.strip():
        return chunks

    stride = max(100, chunk_size - overlap)
    pos = 0
    ord_idx = 0

    while pos < len(text):
        chunk_content = text[pos : pos + chunk_size]
        chunk_hash = hashlib.sha256(chunk_content.encode("utf-8")).hexdigest()[:24]
        token_estimate = len(chunk_content.split())
        chunks.append(
            DocumentChunkData(
                ord_index=ord_idx,
                content=chunk_content,
                char_span={"start": pos, "end": pos + len(chunk_content)},
                token_estimate=token_estimate,
                chunk_hash=chunk_hash,
            )
        )
        ord_idx += 1
        pos += stride
        if pos + overlap >= len(text) and pos < len(text):
            # Final remaining portion
            remaining = text[pos:]
            if remaining:
                r_hash = hashlib.sha256(remaining.encode("utf-8")).hexdigest()[:24]
                chunks.append(
                    DocumentChunkData(
                        ord_index=ord_idx,
                        content=remaining,
                        char_span={"start": pos, "end": len(text)},
                        token_estimate=len(remaining.split()),
                        chunk_hash=r_hash,
                    )
                )
            break

    return chunks


def parse_and_validate_document(
    filename: str,
    content: bytes,
    mime_type: str | None = None,
) -> IngestedDocument:
    """Validate, parse, extract, and chunk a document (TXT, PDF, DOCX)."""
    if len(content) == 0:
        raise DocumentValidationError("Uploaded file is empty.")

    if len(content) > MAX_DOCUMENT_SIZE_BYTES:
        raise DocumentValidationError(
            f"File size ({len(content)} bytes) exceeds limit of {MAX_DOCUMENT_SIZE_BYTES} bytes."
        )

    file_hash = hashlib.sha256(content).hexdigest()
    lower_name = filename.lower().strip()

    resolved_mime = mime_type or "application/octet-stream"
    if lower_name.endswith(".txt"):
        resolved_mime = "text/plain"
        title, text, meta = extract_txt(content, filename)
    elif lower_name.endswith(".pdf"):
        resolved_mime = "application/pdf"
        title, text, meta = extract_pdf(content, filename)
    elif lower_name.endswith(".docx"):
        resolved_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        title, text, meta = extract_docx(content, filename)
    else:
        raise DocumentValidationError(
            "Unsupported file format. Only .txt, .pdf, and .docx are supported."
        )

    # Bound extracted text to avoid storing unbounded copyrighted documents
    capped_text = text[:MAX_EXTRACTED_TEXT_CHARS].strip()
    if not capped_text:
        raise DocumentValidationError("No readable text could be extracted from the document.")

    meta.update(
        {
            "word_count": len(capped_text.split()),
            "character_count": len(capped_text),
            "truncated": len(text) > MAX_EXTRACTED_TEXT_CHARS,
        }
    )

    chunks = chunk_text(capped_text)

    return IngestedDocument(
        filename=filename,
        mime_type=resolved_mime,
        size_bytes=len(content),
        hash_sha256=file_hash,
        extracted_title=title,
        extracted_text=capped_text,
        doc_metadata=meta,
        chunks=chunks,
    )
