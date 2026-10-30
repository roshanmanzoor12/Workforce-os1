from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.client import Config
from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    EndpointConnectionError,
)

from app.config import settings
from app.core.exceptions import StorageError
from app.core.logging import get_logger


logger = get_logger(__name__)


# =========================================================
# S3 / MINIO CLIENT
# =========================================================

def create_client():
    """
    Create and return an S3-compatible client.

    Works with:
    - MinIO in development
    - AWS S3 in production
    - other S3-compatible storage providers
    """

    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint or None,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        use_ssl=settings.s3_use_ssl,
        config=Config(
            signature_version="s3v4",
            connect_timeout=5,
            read_timeout=30,
            retries={
                "max_attempts": 3,
                "mode": "standard",
            },
        ),
    )


# =========================================================
# BUCKET NAME
# =========================================================

def get_bucket_name() -> str:
    """
    Return configured WorkforceOS storage bucket.
    """

    bucket = settings.s3_bucket.strip()

    if not bucket:
        raise StorageError(
            "S3_BUCKET is not configured."
        )

    return bucket


# =========================================================
# HEALTH CHECK
# =========================================================

def check_storage() -> bool:
    """
    Check whether object storage is reachable.

    Returns:
        True  -> storage reachable
        False -> storage unavailable
    """

    try:
        client = create_client()

        client.list_buckets()

        return True

    except Exception as exc:
        logger.error(
            "storage_health_check_failed",
            error=str(exc),
        )

        return False


def test_storage_connection() -> None:
    """
    Raise StorageError if storage is unavailable.

    Intended for startup/readiness checks.
    """

    if not check_storage():
        raise StorageError(
            "Unable to connect to WorkforceOS object storage."
        )


# =========================================================
# BUCKET MANAGEMENT
# =========================================================

def bucket_exists(
    bucket_name: str | None = None,
) -> bool:
    """
    Check whether a bucket exists and is accessible.
    """

    bucket = bucket_name or get_bucket_name()

    try:
        client = create_client()

        client.head_bucket(
            Bucket=bucket,
        )

        return True

    except ClientError as exc:
        code = str(
            exc.response.get(
                "Error",
                {},
            ).get(
                "Code",
                "",
            )
        )

        if code in {
            "404",
            "NoSuchBucket",
            "NotFound",
        }:
            return False

        logger.error(
            "storage_bucket_check_failed",
            bucket=bucket,
            error=str(exc),
        )

        return False

    except Exception as exc:
        logger.error(
            "storage_bucket_check_failed",
            bucket=bucket,
            error=str(exc),
        )

        return False


def ensure_bucket(
    bucket_name: str | None = None,
) -> str:
    """
    Ensure the configured bucket exists.

    Creates it when missing.

    Returns:
        Bucket name.
    """

    bucket = bucket_name or get_bucket_name()

    try:
        client = create_client()

        if bucket_exists(bucket):
            return bucket

        if settings.s3_region == "us-east-1":
            client.create_bucket(
                Bucket=bucket,
            )

        else:
            client.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={
                    "LocationConstraint": settings.s3_region,
                },
            )

        logger.info(
            "storage_bucket_created",
            bucket=bucket,
        )

        return bucket

    except (
        ClientError,
        BotoCoreError,
        EndpointConnectionError,
    ) as exc:
        logger.exception(
            "storage_bucket_creation_failed",
            bucket=bucket,
            error=str(exc),
        )

        raise StorageError(
            f"Unable to create storage bucket '{bucket}'."
        ) from exc


# =========================================================
# OBJECT KEY HELPERS
# =========================================================

def normalize_object_key(
    object_key: str,
) -> str:
    """
    Normalize an S3 object key.

    Removes accidental leading slashes and duplicate separators.
    """

    key = object_key.replace("\\", "/").strip()

    while "//" in key:
        key = key.replace("//", "/")

    return key.lstrip("/")


def build_object_key(
    *parts: str,
) -> str:
    """
    Create a normalized object key.

    Example:

        build_object_key(
            "workspaces",
            workspace_id,
            "employees",
            employee_id,
            "avatar.png",
        )
    """

    clean = [
        str(part).strip("/\\ ")
        for part in parts
        if str(part).strip("/\\ ")
    ]

    return normalize_object_key(
        "/".join(clean)
    )


# =========================================================
# UPLOAD BYTES
# =========================================================

def upload_bytes(
    *,
    object_key: str,
    data: bytes,
    content_type: str = "application/octet-stream",
    bucket_name: str | None = None,
    metadata: dict[str, str] | None = None,
) -> str:
    """
    Upload bytes into S3/MinIO.

    Returns:
        normalized object key
    """

    bucket = bucket_name or get_bucket_name()
    key = normalize_object_key(object_key)

    try:
        ensure_bucket(bucket)

        client = create_client()

        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            Metadata=metadata or {},
        )

        logger.info(
            "storage_object_uploaded",
            bucket=bucket,
            object_key=key,
            size_bytes=len(data),
        )

        return key

    except (
        ClientError,
        BotoCoreError,
        EndpointConnectionError,
    ) as exc:
        logger.exception(
            "storage_upload_failed",
            bucket=bucket,
            object_key=key,
            error=str(exc),
        )

        raise StorageError(
            "Failed to upload object to storage."
        ) from exc


# =========================================================
# UPLOAD FILE OBJECT
# =========================================================

def upload_fileobj(
    *,
    object_key: str,
    file_obj: BinaryIO,
    content_type: str = "application/octet-stream",
    bucket_name: str | None = None,
    metadata: dict[str, str] | None = None,
) -> str:
    """
    Upload an already-open file-like object.

    Useful for:
    - FastAPI UploadFile
    - generated PDFs
    - screenshots
    - resume files
    """

    bucket = bucket_name or get_bucket_name()
    key = normalize_object_key(object_key)

    try:
        ensure_bucket(bucket)

        client = create_client()

        extra_args = {
            "ContentType": content_type,
        }

        if metadata:
            extra_args["Metadata"] = metadata

        client.upload_fileobj(
            file_obj,
            bucket,
            key,
            ExtraArgs=extra_args,
        )

        logger.info(
            "storage_fileobj_uploaded",
            bucket=bucket,
            object_key=key,
        )

        return key

    except (
        ClientError,
        BotoCoreError,
        EndpointConnectionError,
    ) as exc:
        logger.exception(
            "storage_fileobj_upload_failed",
            bucket=bucket,
            object_key=key,
            error=str(exc),
        )

        raise StorageError(
            "Failed to upload file to storage."
        ) from exc


# =========================================================
# UPLOAD LOCAL FILE
# =========================================================

def upload_local_file(
    *,
    local_path: str | Path,
    object_key: str,
    content_type: str = "application/octet-stream",
    bucket_name: str | None = None,
) -> str:
    """
    Upload a local file from disk.

    Mainly useful for:
    - background jobs
    - generated reports
    - migration/import scripts
    """

    path = Path(local_path)

    if not path.exists():
        raise StorageError(
            f"Local file does not exist: {path}"
        )

    if not path.is_file():
        raise StorageError(
            f"Path is not a file: {path}"
        )

    with path.open("rb") as file_obj:
        return upload_fileobj(
            object_key=object_key,
            file_obj=file_obj,
            content_type=content_type,
            bucket_name=bucket_name,
        )


# =========================================================
# DOWNLOAD
# =========================================================

def download_bytes(
    *,
    object_key: str,
    bucket_name: str | None = None,
) -> bytes:
    """
    Download object contents into memory.
    """

    bucket = bucket_name or get_bucket_name()
    key = normalize_object_key(object_key)

    try:
        client = create_client()

        result = client.get_object(
            Bucket=bucket,
            Key=key,
        )

        body = result["Body"].read()

        return body

    except (
        ClientError,
        BotoCoreError,
        EndpointConnectionError,
    ) as exc:
        logger.exception(
            "storage_download_failed",
            bucket=bucket,
            object_key=key,
            error=str(exc),
        )

        raise StorageError(
            "Failed to download object from storage."
        ) from exc


def download_to_file(
    *,
    object_key: str,
    destination: str | Path,
    bucket_name: str | None = None,
) -> Path:
    """
    Download an object to a local file.
    """

    bucket = bucket_name or get_bucket_name()
    key = normalize_object_key(object_key)

    destination_path = Path(destination)

    destination_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        client = create_client()

        client.download_file(
            bucket,
            key,
            str(destination_path),
        )

        return destination_path

    except (
        ClientError,
        BotoCoreError,
        EndpointConnectionError,
    ) as exc:
        logger.exception(
            "storage_file_download_failed",
            bucket=bucket,
            object_key=key,
            destination=str(destination_path),
            error=str(exc),
        )

        raise StorageError(
            "Failed to download storage object."
        ) from exc


# =========================================================
# OBJECT EXISTS
# =========================================================

def object_exists(
    *,
    object_key: str,
    bucket_name: str | None = None,
) -> bool:
    """
    Check whether an object exists.
    """

    bucket = bucket_name or get_bucket_name()
    key = normalize_object_key(object_key)

    try:
        client = create_client()

        client.head_object(
            Bucket=bucket,
            Key=key,
        )

        return True

    except ClientError as exc:
        code = str(
            exc.response.get(
                "Error",
                {},
            ).get(
                "Code",
                "",
            )
        )

        if code in {
            "404",
            "NoSuchKey",
            "NotFound",
        }:
            return False

        logger.warning(
            "storage_object_exists_check_failed",
            bucket=bucket,
            object_key=key,
            error=str(exc),
        )

        return False

    except Exception as exc:
        logger.warning(
            "storage_object_exists_check_failed",
            bucket=bucket,
            object_key=key,
            error=str(exc),
        )

        return False


# =========================================================
# OBJECT METADATA
# =========================================================

def get_object_metadata(
    *,
    object_key: str,
    bucket_name: str | None = None,
) -> dict:
    """
    Return object metadata.

    Useful for:
    - file size
    - MIME type
    - last modified
    - ETag
    """

    bucket = bucket_name or get_bucket_name()
    key = normalize_object_key(object_key)

    try:
        client = create_client()

        result = client.head_object(
            Bucket=bucket,
            Key=key,
        )

        return {
            "object_key": key,
            "size_bytes": result.get(
                "ContentLength"
            ),
            "content_type": result.get(
                "ContentType"
            ),
            "etag": result.get(
                "ETag"
            ),
            "last_modified": result.get(
                "LastModified"
            ),
            "metadata": result.get(
                "Metadata",
                {},
            ),
        }

    except (
        ClientError,
        BotoCoreError,
        EndpointConnectionError,
    ) as exc:
        logger.exception(
            "storage_metadata_failed",
            bucket=bucket,
            object_key=key,
            error=str(exc),
        )

        raise StorageError(
            "Failed to read storage object metadata."
        ) from exc


# =========================================================
# DELETE OBJECT
# =========================================================

def delete_object(
    *,
    object_key: str,
    bucket_name: str | None = None,
) -> None:
    """
    Delete one object from storage.
    """

    bucket = bucket_name or get_bucket_name()
    key = normalize_object_key(object_key)

    try:
        client = create_client()

        client.delete_object(
            Bucket=bucket,
            Key=key,
        )

        logger.info(
            "storage_object_deleted",
            bucket=bucket,
            object_key=key,
        )

    except (
        ClientError,
        BotoCoreError,
        EndpointConnectionError,
    ) as exc:
        logger.exception(
            "storage_delete_failed",
            bucket=bucket,
            object_key=key,
            error=str(exc),
        )

        raise StorageError(
            "Failed to delete object from storage."
        ) from exc


# =========================================================
# PRESIGNED DOWNLOAD URL
# =========================================================

def generate_download_url(
    *,
    object_key: str,
    bucket_name: str | None = None,
    expires_in: int | None = None,
) -> str:
    """
    Generate temporary private download URL.

    Do not make screenshots/resumes/etc public.
    """

    bucket = bucket_name or get_bucket_name()
    key = normalize_object_key(object_key)

    expiry = (
        expires_in
        or settings.s3_presigned_url_expiry_seconds
    )

    if expiry <= 0:
        raise ValueError(
            "Presigned URL expiry must be greater than 0."
        )

    try:
        client = create_client()

        return client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": bucket,
                "Key": key,
            },
            ExpiresIn=expiry,
        )

    except (
        ClientError,
        BotoCoreError,
    ) as exc:
        logger.exception(
            "storage_presigned_download_failed",
            bucket=bucket,
            object_key=key,
            error=str(exc),
        )

        raise StorageError(
            "Failed to create temporary download URL."
        ) from exc


# =========================================================
# PRESIGNED UPLOAD URL
# =========================================================

def generate_upload_url(
    *,
    object_key: str,
    content_type: str = "application/octet-stream",
    bucket_name: str | None = None,
    expires_in: int | None = None,
) -> str:
    """
    Generate temporary direct-upload URL.

    Later useful for large:
    - recordings
    - screenshots
    - resumes
    - documents

    so the API does not need to proxy every byte.
    """

    bucket = bucket_name or get_bucket_name()
    key = normalize_object_key(object_key)

    expiry = (
        expires_in
        or settings.s3_presigned_url_expiry_seconds
    )

    if expiry <= 0:
        raise ValueError(
            "Presigned URL expiry must be greater than 0."
        )

    try:
        ensure_bucket(bucket)

        client = create_client()

        return client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=expiry,
        )

    except (
        ClientError,
        BotoCoreError,
    ) as exc:
        logger.exception(
            "storage_presigned_upload_failed",
            bucket=bucket,
            object_key=key,
            error=str(exc),
        )

        raise StorageError(
            "Failed to create temporary upload URL."
        ) from exc


# =========================================================
# LIST OBJECTS
# =========================================================

def list_objects(
    *,
    prefix: str = "",
    bucket_name: str | None = None,
    max_keys: int = 100,
) -> list[dict]:
    """
    List storage objects under a prefix.

    Intended mainly for internal/admin/debugging jobs.
    Business APIs should normally read file metadata from PostgreSQL.
    """

    bucket = bucket_name or get_bucket_name()

    normalized_prefix = (
        normalize_object_key(prefix)
        if prefix
        else ""
    )

    try:
        client = create_client()

        result = client.list_objects_v2(
            Bucket=bucket,
            Prefix=normalized_prefix,
            MaxKeys=max_keys,
        )

        objects = []

        for item in result.get(
            "Contents",
            [],
        ):
            objects.append(
                {
                    "object_key": item.get(
                        "Key"
                    ),
                    "size_bytes": item.get(
                        "Size"
                    ),
                    "last_modified": item.get(
                        "LastModified"
                    ),
                    "etag": item.get(
                        "ETag"
                    ),
                }
            )

        return objects

    except (
        ClientError,
        BotoCoreError,
        EndpointConnectionError,
    ) as exc:
        logger.exception(
            "storage_list_objects_failed",
            bucket=bucket,
            prefix=normalized_prefix,
            error=str(exc),
        )

        raise StorageError(
            "Failed to list storage objects."
        ) from exc