"""
DocumentParser leveraging LangChain loaders.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, Type

from langchain_community.document_loaders import (
    BSHTMLLoader,
    Docx2txtLoader,
    PyPDFLoader,
    TextLoader,
)
from langchain_core.documents import Document as LCDocument


class DocumentParser:
    """Parse various document formats into raw text using LangChain loaders."""

    def __init__(self) -> None:
        self._loader_map: Dict[str, Type] = {
            "pdf": PyPDFLoader,
            "docx": Docx2txtLoader,
            "doc": Docx2txtLoader,
            "html": BSHTMLLoader,
            "htm": BSHTMLLoader,
            "txt": TextLoader,
            "md": TextLoader,
        }

    async def parse(self, filename: str, content: bytes) -> str:
        """Parse document bytes to text asynchronously."""
        return await asyncio.to_thread(self._parse_sync, filename, content)

    def _parse_sync(self, filename: str, content: bytes) -> str:
        ext = Path(filename).suffix.lower().lstrip(".")
        loader_cls = self._loader_map.get(ext, TextLoader)

        suffix = f".{ext}" if ext else ""
        with NamedTemporaryFile(delete=True, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_file.flush()

            if loader_cls in (TextLoader,):
                loader = loader_cls(temp_file.name, autodetect_encoding=True)
            else:
                loader = loader_cls(temp_file.name)

            docs: list[LCDocument] = loader.load()
            return "\n\n".join(doc.page_content for doc in docs if doc.page_content)

