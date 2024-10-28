from minio import Minio
import os

MINIO_URL = "nginx:9000"
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
BUCKET_NAME = "telegram-bucket"

minio_client = Minio(
    MINIO_URL,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)


def upload_file(file_path, object_name):
    """Uploads a file to MinIO."""
    minio_client.fput_object(BUCKET_NAME, object_name, file_path)
    return f"{MINIO_URL}/{BUCKET_NAME}/{object_name}"
