from minio import Minio
from datetime import timedelta

from src.core.config import settings

class MinioService:
    def __init__(self):
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )

    def upload_file(
            self,
            bucket_name: str,
            object_name: str,
            file_path: str
    ) -> None:
        self.client.fput_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=file_path
        )

    def delete_file(
            self,
            bucket_name: str,
            object_name: str
    ) -> None:
        self.client.remove_object(
            bucket_name=bucket_name,
            object_name=object_name
        )

    def get_presigned_url(
            self,
            bucket_name: str,
            object_name: str
    ) -> str:
        return self.client.presigned_get_object(
            bucket_name=bucket_name,
            object_name=object_name,
            expires=timedelta(hours=1)
        )

minio_service = MinioService()