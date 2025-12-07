"""
MinIO Storage Service
"""
from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Tuple, Optional
from urllib.parse import urlparse

from minio import Minio
from minio.error import S3Error

from src.config.settings import get_settings, Settings


class MinioStorageService:
    """Helper around MinIO client for presigned uploads."""

    def __init__(self, settings: Settings | None = None):
        self._settings = settings or get_settings()
        self._bucket = self._settings.minio_bucket

        internal_endpoint, internal_secure = self._parse_endpoint(
            self._settings.minio_endpoint,
            self._settings.minio_secure,
        )

        self._client = Minio(
            endpoint=internal_endpoint,
            access_key=self._settings.minio_access_key,
            secret_key=self._settings.minio_secret_key,
            secure=internal_secure,
        )

        self._external_base_url: Optional[str] = None
        if self._settings.minio_external_endpoint:
            ext_endpoint, ext_secure = self._parse_endpoint(
                self._settings.minio_external_endpoint,
                self._settings.minio_secure,
            )
            protocol = "https" if ext_secure else "http"
            self._external_base_url = f"{protocol}://{ext_endpoint}".rstrip("/")
        self._ensure_bucket()

    @staticmethod
    def _parse_endpoint(endpoint: str, secure_default: bool) -> Tuple[str, bool]:
        """Parse endpoint string, allowing http(s)://host:port or host:port style."""
        endpoint = endpoint.strip()
        
        if "://" in endpoint:
            parsed = urlparse(endpoint)
            host = parsed.netloc or parsed.path
            secure = parsed.scheme == "https"
            return host, secure
        
        if ":" in endpoint:
            return endpoint, secure_default
        else:
            return f"{endpoint}:9000", secure_default

    def _ensure_bucket(self) -> None:
        """Create bucket if it does not exist."""
        import logging
        logger = logging.getLogger(__name__)
        try:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket)
                logger.info(f"Created MinIO bucket: {self._bucket}")
        except S3Error as exc: 
            if exc.code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
                logger.warning(f"MinIO bucket check failed: {exc}. Will retry on first use.")
        except Exception as exc:  
            logger.warning(f"MinIO connection error during initialization: {exc}. Will retry on first use.")

    def generate_presigned_upload_url(
        self,
        object_name: str,
        expires: timedelta | None = None,
    ) -> tuple[str, int]:
        """
        Generate a presigned PUT URL for direct uploads.

        Returns the URL and expiry (seconds).
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            self._ensure_bucket()
        except Exception as e:
            logger.warning(f"Bucket check failed, continuing anyway: {e}")
        
        expiry = expires or timedelta(minutes=15)
        try:
            url = self._client.presigned_put_object(self._bucket, object_name, expires=expiry)
            return url, int(expiry.total_seconds())
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise

    def get_object_url(self, object_name: str) -> str:
        """Return a direct (unsigned) URL if public, otherwise presigned GET URL."""
        if self._settings.minio_secure:
            return self._client.presigned_get_object(
                self._bucket, object_name, expires=timedelta(minutes=5)
            )

        if self._external_base_url:
            base_url = self._external_base_url
        else:
            internal_endpoint, internal_secure = self._parse_endpoint(
                self._settings.minio_endpoint,
                self._settings.minio_secure,
            )
            protocol = "https" if internal_secure else "http"
            base_url = f"{protocol}://{internal_endpoint}"
        return f"{base_url.rstrip('/')}/{self._bucket}/{object_name}"

    async def download_object(self, object_name: str) -> bytes:
        """Download object bytes."""

        def _download() -> bytes:
            resp = self._client.get_object(self._bucket, object_name)
            try:
                return resp.read()
            finally:
                resp.close()
                resp.release_conn()

        return await asyncio.to_thread(_download)


