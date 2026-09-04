"""Unit tests for document ingestion, safe parsing, and document API routes."""

import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.documents import (
    DocumentValidationError,
    chunk_text,
    extract_docx,
    extract_pdf,
    extract_txt,
    parse_and_validate_document,
)


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client


def _make_sample_docx(text: str = "IdeaLens: Autonomous Technical Research Engine") -> bytes:
    """Create a minimal valid in-memory DOCX file."""
    buf = io.BytesIO()
    types_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        '  <Default Extension="xml" ContentType="application/xml"/>\n'
        '  <Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        '  <Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>\n'
        '</Types>'
    )
    core_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<cp:coreProperties xmlns:cp='
        '"http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        '  <dc:title>Sample Research Proposal</dc:title>\n'
        '</cp:coreProperties>'
    )
    doc_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
        '  <w:body>\n'
        f'    <w:p><w:r><w:t>{text}</w:t></w:r></w:p>\n'
        '    <w:p><w:r><w:t>Second paragraph describing method and results.</w:t></w:r></w:p>\n'
        '  </w:body>\n'
        '</w:document>'
    )
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", types_xml)
        zf.writestr("docProps/core.xml", core_xml)
        zf.writestr("word/document.xml", doc_xml)
    return buf.getvalue()


def _make_sample_pdf(text: str = "Autonomous Evidence Extraction Framework") -> bytes:
    """Create a minimal valid in-memory PDF file."""
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog /Pages 2 0 R >>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\n"
        b"endobj\n"
        b"4 0 obj\n"
        b"<< /Length 55 >>\n"
        b"stream\n"
        b"BT\n"
        b"/F1 12 Tf\n"
        b"100 700 Td\n"
        b"(" + text.encode("ascii") + b") Tj\n"
        b"ET\n"
        b"endstream\n"
        b"endobj\n"
        b"5 0 obj\n"
        b"<< /Title (Sample PDF Proposal) >>\n"
        b"endobj\n"
        b"xref\n"
        b"0 6\n"
        b"0000000000 65535 f \n"
        b"trailer\n"
        b"<< /Size 6 /Root 1 0 R /Info 5 0 R >>\n"
        b"startxref\n"
        b"400\n"
        b"%%EOF\n"
    )
    return content


def test_extract_txt_valid():
    raw = (
        b"IdeaLens Proposal\n"
        b"We present a decentralized consensus mechanism for high-throughput IoT."
    )
    title, text, meta = extract_txt(raw, "proposal.txt")
    assert title == "IdeaLens Proposal"
    assert "decentralized consensus" in text
    assert meta["line_count"] == 2


def test_extract_docx_valid():
    docx_bytes = _make_sample_docx("Novel Federated Multi-Task Optimization")
    title, text, meta = extract_docx(docx_bytes, "proposal.docx")
    assert title == "Sample Research Proposal"
    assert "Novel Federated Multi-Task Optimization" in text
    assert meta["paragraph_count"] == 2


def test_extract_pdf_valid():
    pdf_bytes = _make_sample_pdf("Autonomous Graph Traversal with Latency Guarantees")
    title, text, meta = extract_pdf(pdf_bytes, "proposal.pdf")
    assert title == "Sample PDF Proposal"
    assert "Autonomous Graph Traversal" in text


def test_reject_dangerous_executables():
    with pytest.raises(DocumentValidationError, match="Executable binaries"):
        parse_and_validate_document("malicious.txt", b"MZ\x90\x00executable content")

    with pytest.raises(DocumentValidationError, match="Executable binaries"):
        parse_and_validate_document("malicious.pdf", b"\x7fELFsomething")


def test_reject_unsupported_format():
    with pytest.raises(DocumentValidationError, match="Unsupported file format"):
        parse_and_validate_document("archive.tar.gz", b"some binary data")


def test_chunking_text():
    sample_text = "word " * 600  # ~3000 chars
    chunks = chunk_text(sample_text, chunk_size=1000, overlap=100)
    assert len(chunks) >= 3
    assert chunks[0].ord_index == 0
    assert chunks[0].chunk_hash != ""


def test_document_upload_and_get_api(client):
    docx_bytes = _make_sample_docx("Zero-Knowledge Machine Learning Verification")
    docx_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    files = {"file": ("proposal.docx", docx_bytes, docx_mime)}

    response = client.post("/api/v1/documents/upload", files=files)
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "proposal.docx"
    assert body["extracted_title"] == "Sample Research Proposal"
    assert "Zero-Knowledge" in body["extracted_text"]
    assert body["chunks_count"] >= 1
    doc_id = body["id"]

    # Retrieve uploaded doc
    get_res = client.get(f"/api/v1/documents/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == doc_id


def test_create_run_with_document_id(client):
    sample_idea = "Graph Neural Networks for Scalable Quantum Chemistry Simulations."
    txt_content = sample_idea.encode("utf-8")
    files = {"file": ("idea.txt", txt_content, "text/plain")}

    upload_res = client.post("/api/v1/documents/upload", files=files)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # Start run referencing document_id
    run_res = client.post(
        "/api/v1/research-runs",
        json={
            "idea": sample_idea,
            "document_id": doc_id,
        },
    )
    assert run_res.status_code == 202
    body = run_res.json()
    assert body["source_document_id"] == doc_id
    assert body["decomposition"] is not None
    assert "objective" in body["decomposition"]
    assert "technologies" in body["decomposition"]
