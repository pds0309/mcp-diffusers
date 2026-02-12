import os
import io
from minio import Minio
from datetime import datetime
import uuid


class Storage:
    def __init__(self):
        # Load configuration from environment variables
        self.endpoint = os.environ.get("MINIO_ENDPOINT", "localhost:9000")
        # remove protocol if present for minio client initialization
        if self.endpoint.startswith("http://"):
            self.endpoint = self.endpoint.replace("http://", "")
        elif self.endpoint.startswith("https://"):
            self.endpoint = self.endpoint.replace("https://", "")

        self.access_key = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
        self.secret_key = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
        self.bucket_name = os.environ.get("MINIO_BUCKET_NAME", "zimage")
        self.external_endpoint = os.environ.get("MINIO_EXTERNAL_ENDPOINT", "http://localhost:9000")

        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=False  # Assumed local/dev setup based on .env
        )

        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        if not self.client.bucket_exists(self.bucket_name):
            self.client.make_bucket(self.bucket_name)

    def upload_image(self, image_data: bytes, ext: str = "png") -> str:
        """
        Uploads image bytes to MinIO and returns the public URL.
        """
        filename = f"{datetime.now().strftime('%Y%m%d')}/{uuid.uuid4()}.{ext}"

        # Wrap bytes in a file-like object
        data_stream = io.BytesIO(image_data)

        self.client.put_object(
            self.bucket_name,
            filename,
            data_stream,
            length=len(image_data),
            content_type=f"image/{ext}"
        )

        # Construct public URL
        # Assuming the external endpoint is accessible and mapped correctly
        return f"{self.external_endpoint}/{self.bucket_name}/{filename}"
