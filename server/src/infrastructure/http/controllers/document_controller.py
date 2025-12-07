"""
DocumentController - Infrastructure Layer (HTTP)
Single Responsibility: Handle HTTP requests for document operations
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
import re
from typing import List
from uuid import uuid4
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, BackgroundTasks
from pydantic import BaseModel, Field

from src.application.usecases.IndexDocumentUseCase import IndexDocumentUseCase
from src.application.usecases.UploadFileUseCase import UploadFileUseCase
from src.domain.entities.Document import Document, DocumentStatus
from src.domain.repositories.DocumentRepository import DocumentRepository
from src.infrastructure.database.postgres.models import UserModel
from src.infrastructure.http.dependencies import (
    get_document_repository,
    get_index_document_use_case,
    get_upload_file_use_case,
    get_storage_service,
    get_document_ingestion_service,
)
from src.infrastructure.security.auth import get_current_user
from src.infrastructure.storage.minio_storage import MinioStorageService
from src.application.services.DocumentIngestionService import DocumentIngestionService

router = APIRouter(prefix="/api/documents", tags=["Documents"], redirect_slashes=False)


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    uploaded_at: str
    indexed_at: str | None = None
    chunk_count: int | None = None
    error_message: str | None = None
    group_id: str | None = None  # Add group_id field

    @classmethod
    def from_entity(cls, document: Document) -> "DocumentResponse":
        return cls(
            id=document.id,
            filename=document.filename,
            file_type=document.file_type,
            file_size=document.file_size,
            status=document.status,
            uploaded_at=document.uploaded_at.isoformat(),
            indexed_at=document.indexed_at.isoformat() if document.indexed_at else None,
            chunk_count=document.chunk_count,
            error_message=document.error_message,
            group_id=document.group_id,
        )


class UploadFileDescriptor(BaseModel):
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    file_size: int = Field(..., gt=0, description="File size in bytes (client-side)")


class UploadRequest(BaseModel):
    files: List[UploadFileDescriptor]
    group_id: str | None = None  # Optional group to assign documents to


class UploadRequestItemResponse(BaseModel):
    document_id: str
    filename: str
    content_type: str
    upload_url: str
    storage_key: str
    expires_in: int


class UploadRequestResponse(BaseModel):
    uploads: List[UploadRequestItemResponse]


class UploadConfirmRequest(BaseModel):
    document_id: str
    file_size: int = Field(..., gt=0)
    checksum: str | None = None
    metadata: dict | None = None
    group_id: str | None = None  # Optional group to assign document to


def _sanitize_filename(filename: str) -> str:
    """Return a filesystem-safe filename."""
    name = Path(filename).name
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return safe[:255] or f"file_{uuid4().hex}"


def _build_storage_key(user_id: str, document_id: str, filename: str) -> str:
    """Build a deterministic storage key for the uploaded object."""
    safe_name = _sanitize_filename(filename)
    return f"{user_id}/{document_id}/{safe_name}"


@router.get("", response_model=List[DocumentResponse])
@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    document_repository: DocumentRepository = Depends(get_document_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """List documents for the current user."""
    try:
        documents = await document_repository.get_by_user_id(str(current_user.id))
        return [DocumentResponse.from_entity(doc) for doc in documents]
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        ) from e


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    document_repository: DocumentRepository = Depends(get_document_repository),
):
    """Get a single document."""
    document = await document_repository.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.from_entity(document)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    document_repository: DocumentRepository = Depends(get_document_repository),
):
    """Delete a document."""
    deleted = await document_repository.delete(document_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return None


@router.post("/{document_id}/reindex", response_model=DocumentResponse)
async def reindex_document(
    document_id: str,
    index_use_case: IndexDocumentUseCase = Depends(get_index_document_use_case),
):
    """Re-run indexing for a document."""
    document = await index_use_case.execute(document_id)
    return DocumentResponse.from_entity(document)


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    upload_use_case: UploadFileUseCase = Depends(get_upload_file_use_case),
    document_repository: DocumentRepository = Depends(get_document_repository),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Upload and index a document.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    try:
        document = await upload_use_case.execute(
            user_id=str(current_user.id),
            filename=file.filename,
            file_content=BytesIO(file_bytes),
            file_size=len(file_bytes),
        )

        # Upload use case already triggers indexing; fetch latest state
        refreshed = await document_repository.get_by_id(document.id)
        return DocumentResponse.from_entity(refreshed or document)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/upload-request", response_model=UploadRequestResponse)
async def create_upload_request(
    payload: UploadRequest,
    document_repository: DocumentRepository = Depends(get_document_repository),
    storage_service: MinioStorageService = Depends(get_storage_service),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Generate pre-signed URLs so the client can upload large files directly to object storage.
    """
    if not payload.files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No files supplied")

    uploads: List[UploadRequestItemResponse] = []
    for descriptor in payload.files:
        document_id = str(uuid4())
        storage_key = _build_storage_key(str(current_user.id), document_id, descriptor.filename)
        upload_url, expires_in = storage_service.generate_presigned_upload_url(storage_key)

        document = Document(
            id=document_id,
            user_id=str(current_user.id),
            filename=descriptor.filename,
            file_type=descriptor.content_type,
            file_size=descriptor.file_size,
            status=DocumentStatus.PENDING,
            uploaded_at=datetime.now(timezone.utc),
            metadata={
                "storage_key": storage_key,
                "upload_expires_in": expires_in,
            },
            group_id=payload.group_id,
        )
        await document_repository.create(document)
        uploads.append(
            UploadRequestItemResponse(
                document_id=document_id,
                filename=descriptor.filename,
                content_type=descriptor.content_type,
                upload_url=upload_url,
                storage_key=storage_key,
                expires_in=expires_in,
            )
        )

    return UploadRequestResponse(uploads=uploads)


@router.post("/upload/confirm", response_model=DocumentResponse)
async def confirm_upload(
    payload: UploadConfirmRequest,
    background_tasks: BackgroundTasks,
    document_repository: DocumentRepository = Depends(get_document_repository),
    ingestion_service: DocumentIngestionService = Depends(get_document_ingestion_service),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Confirm that the client has finished uploading a file to object storage.
    """
    document = await document_repository.get_by_id(payload.document_id)
    if not document or document.user_id != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    metadata = payload.metadata.copy() if payload.metadata else {}
    metadata["upload_confirmed"] = True
    metadata["upload_confirmed_at"] = datetime.now(timezone.utc).isoformat()
    if payload.checksum:
        metadata["checksum"] = payload.checksum

    updated = await document_repository.update_file_info(
        payload.document_id,
        file_size=payload.file_size,
        metadata=metadata,
        group_id=payload.group_id,
    )

    document_response = DocumentResponse.from_entity(updated)

    background_tasks.add_task(ingestion_service.ingest_document, payload.document_id)
    return document_response

