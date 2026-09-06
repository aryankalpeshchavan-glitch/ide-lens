"""Document upload and text extraction API (DATA_MODEL.md §1.3 & AUTH §1.5)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.auth import CurrentUser
from app.core.rate_limit import rate_limit_upload
from app.core.security import sanitize_filename
from app.db.session import get_session
from app.models.research import DocumentChunkORM, DocumentORM
from app.services.documents import (
    DocumentValidationError,
    parse_and_validate_document,
)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class DocumentUploadResponse(BaseModel):
    id: UUID
    filename: str
    mime_type: str
    size_bytes: int
    hash_sha256: str
    extracted_title: str | None
    extracted_text: str
    word_count: int
    chunks_count: int
    doc_metadata: dict


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_upload)],
)
async def upload_document(
    session: Annotated[Session, Depends(get_session)],
    file: Annotated[UploadFile, File()],
    user_id: CurrentUser,
) -> DocumentUploadResponse:
    """Upload TXT, PDF, or DOCX document and extract structured text safely."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename in upload.")

    safe_filename = sanitize_filename(file.filename)

    try:
        content = await file.read()
        ingested = parse_and_validate_document(
            filename=safe_filename,
            content=content,
            mime_type=file.content_type,
        )
    except DocumentValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "code": exc.code,
                "message": str(exc),
                "details": exc.details,
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SERVER_PROCESSING_ERROR",
                "message": "An unexpected error occurred while processing the document.",
                "details": {"error_type": type(exc).__name__},
            },
        ) from exc

    doc_orm = DocumentORM(
        owner_id=user_id,
        filename=ingested.filename,
        mime_type=ingested.mime_type,
        size_bytes=ingested.size_bytes,
        hash_sha256=ingested.hash_sha256,
        parse_status="parsed",
        extracted_title=ingested.extracted_title,
        extracted_text=ingested.extracted_text,
        doc_metadata=ingested.doc_metadata,
    )
    session.add(doc_orm)
    session.flush()

    for chunk in ingested.chunks:
        chunk_orm = DocumentChunkORM(
            document_id=doc_orm.id,
            ord_index=chunk.ord_index,
            content=chunk.content,
            char_span=chunk.char_span,
            token_estimate=chunk.token_estimate,
            chunk_hash=chunk.chunk_hash,
        )
        session.add(chunk_orm)

    session.commit()
    session.refresh(doc_orm)

    return DocumentUploadResponse(
        id=doc_orm.id,
        filename=doc_orm.filename,
        mime_type=doc_orm.mime_type,
        size_bytes=doc_orm.size_bytes,
        hash_sha256=doc_orm.hash_sha256,
        extracted_title=doc_orm.extracted_title,
        extracted_text=doc_orm.extracted_text,
        word_count=ingested.doc_metadata.get("word_count", 0),
        chunks_count=len(ingested.chunks),
        doc_metadata=doc_orm.doc_metadata or {},
    )


@router.get("/{document_id}", response_model=DocumentUploadResponse)
def get_document(
    document_id: UUID,
    session: Annotated[Session, Depends(get_session)],
    user_id: CurrentUser,
) -> DocumentUploadResponse:
    """Retrieve an ingested document by its UUID, verifying ownership."""
    doc = session.get(DocumentORM, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Authorize ownership boundary
    if doc.owner_id is not None and doc.owner_id != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    chunks_count = (
        session.query(DocumentChunkORM)
        .filter(DocumentChunkORM.document_id == doc.id)
        .count()
    )

    return DocumentUploadResponse(
        id=doc.id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        size_bytes=doc.size_bytes,
        hash_sha256=doc.hash_sha256,
        extracted_title=doc.extracted_title,
        extracted_text=doc.extracted_text,
        word_count=(doc.doc_metadata or {}).get("word_count", 0),
        chunks_count=chunks_count,
        doc_metadata=doc.doc_metadata or {},
    )
