import io
import os
import uuid
from datetime import timedelta

from fastapi import UploadFile
from minio import Minio

from src.core.config import settings


class MinioService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )

    async def put_file(
        self,
        bucket: str,
        file: UploadFile,
        object_name: str | None = None,
        expires_days: int = 7,
    ):
        if object_name is None:
            ext = os.path.splitext(file.filename)[1]
            object_name = f"{uuid.uuid4()}{ext}"

        contents = await file.read()

        self.client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=io.BytesIO(contents),
            length=len(contents),
            content_type=file.content_type,
        )

        url = self.client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_name,
            expires=timedelta(days=expires_days),
        )

        return {"url": url, "object_name": object_name}

    def upload_file(
        self,
        bucket: str,
        file,
        file_path: str,
        object_name: str | None = None,
        expires_days: int = 7,
    ) -> str:
        """
        Загрузить файл в MinIO.

        Returns:
            Pre-signed URL для скачивания
        """
        if object_name is None:
            object_name = os.path.basename(file_path)

        # Upload
        self.client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=file_path,
            content_type=self._get_content_type(file_path),
        )

        # Get pre-signed URL
        url = self.client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_name,
            expires=timedelta(days=expires_days),
        )

        return url

    def download_file(self, bucket: str, object_name: str, file_path: str):
        """Скачать файл из MinIO."""
        self.client.fget_object(
            bucket_name=bucket, object_name=object_name, file_path=file_path
        )

    def delete_file(self, bucket: str, object_name: str):
        """Удалить файл."""
        self.client.remove_object(bucket_name=bucket, object_name=object_name)

    def list_files(self, bucket: str, prefix: str | None = None):
        """Список файлов."""
        return list(
            self.client.list_objects(bucket_name=bucket, prefix=prefix, recursive=True)
        )

    def get_file(self, bucket: str, object_name: str) -> bytes:
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except Exception as e:
            raise ValueError(f"Failed to get file from MinIO: {e!s}")

    def _get_content_type(self, file_path: str) -> str:
        """Определить Content-Type."""
        ext = os.path.splitext(file_path)[1].lower()

        content_types = {
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".csv": "text/csv",
            ".pdf": "application/pdf",
            ".json": "application/json",
        }

        return content_types.get(ext, "application/octet-stream")


minio_service = MinioService()
