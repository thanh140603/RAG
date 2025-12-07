"""
UploadFileUseCase - Application Layer
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from src.application.usecases.IndexDocumentUseCase import IndexDocumentUseCase

from src.domain.entities.Document import Document, DocumentStatus
from src.domain.repositories.DocumentRepository import DocumentRepository
from src.config.settings import get_settings

settings = get_settings()


class UploadFileUseCase:
    """
    Handles validation + persistence of uploaded documents
    """

    def __init__(
        self,
        document_repository: DocumentRepository,
        index_document_use_case: Optional["IndexDocumentUseCase"] = None,
    ):
        self._document_repository = document_repository
        self._index_document_use_case = index_document_use_case
        self._upload_dir = Path(settings.upload_directory)

    async def execute(
        self,
        user_id: str,
        filename: str,
        file_content: BinaryIO,
        file_size: int,
    ) -> Document:
        self._validate_file(filename, file_size)

        document = Document(
            id=str(uuid4()),
            user_id=user_id,
            filename=filename,
            file_type=self._get_file_type(filename),
            file_size=file_size,
            status=DocumentStatus.PENDING,
            uploaded_at=datetime.utcnow(),
        )

        document = await self._document_repository.create(document)
        storage_path = self._build_storage_path(document)
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        if hasattr(file_content, "seek"):
            file_content.seek(0)

        with open(storage_path, "wb") as destination:
            destination.write(file_content.read())

        if self._index_document_use_case:
            await self._index_document_use_case.execute(document.id)

        return document

    def _validate_file(self, filename: str, file_size: int) -> None:
        ext = self._get_file_type(filename)
        allowed = [ft.strip().lower() for ft in settings.allowed_file_types]
        if ext.lower() not in allowed:
            raise ValueError(f"File type '{ext}' is not allowed")
        if file_size > settings.max_file_size:
            raise ValueError("File size exceeds configured maximum")

    def _get_file_type(self, filename: str) -> str:
        return filename.split(".")[-1].lower() if "." in filename else "unknown"

    def _build_storage_path(self, document: Document) -> Path:
        return (
            self._upload_dir
            / document.user_id
            / f"{document.id}_{document.filename}"
        )

