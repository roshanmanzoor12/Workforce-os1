from __future__ import annotations

import io
from datetime import timedelta
from typing import Any

from botocore.exceptions import (
    BotoCoreError,
    ClientError,
    EndpointConnectionError,
)

from app.config import settings
from app.core.storage import (
    create_client,
    ensure_bucket,
    get_bucket_name,
)


# =========================================================
# ERRORS
# =========================================================


class AttachmentStorageError(
    RuntimeError
):
    pass


# =========================================================
# ATTACHMENT STORAGE
# =========================================================


class AttachmentStorage:
    """
    Attachment object-storage adapter.

    This adapter intentionally reuses WorkforceOS' central
    S3-compatible storage configuration instead of maintaining
    a second MINIO_* environment contract.

    Supported backends:

        MinIO
        AWS S3
        other S3-compatible object stores

    Central configuration source:

        settings.s3_endpoint
        settings.s3_access_key
        settings.s3_secret_key
        settings.s3_bucket
        settings.s3_region
        settings.s3_use_ssl

    Attachment object keys are already namespaced by the
    attachment service, so a dedicated physical bucket is not
    required.
    """

    def __init__(
        self,
    ) -> None:
        try:
            self.bucket = (
                get_bucket_name()
            )

            self.client = (
                create_client()
            )

        except Exception as exc:
            raise AttachmentStorageError(
                "Unable to initialize "
                "attachment object storage."
            ) from exc

    # =====================================================
    # BUCKET
    # =====================================================

    def ensure_bucket(
        self,
    ) -> None:
        try:
            ensure_bucket(
                self.bucket
            )

        except Exception as exc:
            raise AttachmentStorageError(
                "Unable to initialize "
                "attachment storage bucket."
            ) from exc

    # =====================================================
    # PRESIGNED UPLOAD
    # =====================================================

    def create_upload_url(
        self,
        *,
        object_key: str,
        expires_seconds: int = 900,
    ) -> str:
        self.ensure_bucket()

        if expires_seconds <= 0:
            raise AttachmentStorageError(
                "Attachment upload URL expiry "
                "must be greater than zero."
            )

        try:
            return str(
                self.client.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={
                        "Bucket": self.bucket,
                        "Key": object_key,
                    },
                    ExpiresIn=int(
                        expires_seconds
                    ),
                )
            )

        except (
            ClientError,
            BotoCoreError,
            EndpointConnectionError,
        ) as exc:
            raise AttachmentStorageError(
                "Unable to create "
                "attachment upload URL."
            ) from exc

        except Exception as exc:
            raise AttachmentStorageError(
                "Unable to create "
                "attachment upload URL."
            ) from exc

    # =====================================================
    # PRESIGNED DOWNLOAD
    # =====================================================

    def create_download_url(
        self,
        *,
        object_key: str,
        expires_seconds: int = 300,
        download_filename: str | None = None,
        content_type: str | None = None,
    ) -> str:
        self.ensure_bucket()

        if expires_seconds <= 0:
            raise AttachmentStorageError(
                "Attachment download URL expiry "
                "must be greater than zero."
            )

        params = {
            "Bucket": self.bucket,
            "Key": object_key,
        }

        if download_filename:
            safe_filename = (
                download_filename
                .replace("\\", "_")
                .replace('"', "'")
                .replace("\r", "_")
                .replace("\n", "_")
            )

            params["ResponseContentDisposition"] = (
                f'attachment; filename="{safe_filename}"'
            )

        if content_type:
            params["ResponseContentType"] = content_type

        try:
            return str(
                self.client.generate_presigned_url(
                    ClientMethod="get_object",
                    Params=params,
                    ExpiresIn=int(expires_seconds),
                )
            )

        except (
            ClientError,
            BotoCoreError,
            EndpointConnectionError,
        ) as exc:
            raise AttachmentStorageError(
                "Unable to create attachment download URL."
            ) from exc

        except Exception as exc:
            raise AttachmentStorageError(
                "Unable to create attachment download URL."
            ) from exc

    # =====================================================
    # OBJECT EXISTS
    # =====================================================

    def object_exists(
        self,
        *,
        object_key: str,
    ) -> bool:
        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=object_key,
            )

            return True

        except ClientError as exc:
            error = (
                exc.response
                .get(
                    "Error",
                    {},
                )
            )

            code = str(
                error.get(
                    "Code",
                    "",
                )
            )

            status_code = (
                exc.response
                .get(
                    "ResponseMetadata",
                    {},
                )
                .get(
                    "HTTPStatusCode"
                )
            )

            if (
                code
                in {
                    "404",
                    "NoSuchKey",
                    "NoSuchObject",
                    "NotFound",
                }
                or status_code == 404
            ):
                return False

            raise AttachmentStorageError(
                "Unable to inspect "
                "attachment object."
            ) from exc

        except (
            BotoCoreError,
            EndpointConnectionError,
        ) as exc:
            raise AttachmentStorageError(
                "Unable to inspect "
                "attachment object."
            ) from exc

        except Exception as exc:
            raise AttachmentStorageError(
                "Unable to inspect "
                "attachment object."
            ) from exc

    # =====================================================
    # OBJECT SIZE
    # =====================================================

    def object_size(
        self,
        *,
        object_key: str,
    ) -> int:
        try:
            response: dict[
                str,
                Any,
            ] = (
                self.client.head_object(
                    Bucket=self.bucket,
                    Key=object_key,
                )
            )

            size = response.get(
                "ContentLength"
            )

            if size is None:
                raise AttachmentStorageError(
                    "Attachment object metadata "
                    "did not contain size."
                )

            return int(
                size
            )

        except AttachmentStorageError:
            raise

        except (
            ClientError,
            BotoCoreError,
            EndpointConnectionError,
        ) as exc:
            raise AttachmentStorageError(
                "Unable to read attachment "
                "object metadata."
            ) from exc

        except Exception as exc:
            raise AttachmentStorageError(
                "Unable to read attachment "
                "object metadata."
            ) from exc

    # =====================================================
    # DELETE
    # =====================================================

    def delete_object(
        self,
        *,
        object_key: str,
    ) -> None:
        try:
            self.client.delete_object(
                Bucket=self.bucket,
                Key=object_key,
            )

        except (
            ClientError,
            BotoCoreError,
            EndpointConnectionError,
        ) as exc:
            raise AttachmentStorageError(
                "Unable to delete "
                "attachment object."
            ) from exc

        except Exception as exc:
            raise AttachmentStorageError(
                "Unable to delete "
                "attachment object."
            ) from exc

    # =====================================================
    # HEALTHCHECK
    # =====================================================

    def healthcheck(
        self,
    ) -> None:
        """
        Verify the complete attachment storage path:

            bucket
                ->
            write
                ->
            head
                ->
            delete
        """

        self.ensure_bucket()

        object_key = (
            "_healthcheck/"
            "attachments-probe.txt"
        )

        payload = b"ok"

        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=object_key,
                Body=io.BytesIO(
                    payload
                ),
                ContentLength=len(
                    payload
                ),
                ContentType="text/plain",
            )

            result = (
                self.client.head_object(
                    Bucket=self.bucket,
                    Key=object_key,
                )
            )

            actual_size = int(
                result.get(
                    "ContentLength",
                    -1,
                )
            )

            if (
                actual_size
                != len(
                    payload
                )
            ):
                raise AttachmentStorageError(
                    "Attachment storage "
                    "healthcheck size mismatch."
                )

        except AttachmentStorageError:
            raise

        except (
            ClientError,
            BotoCoreError,
            EndpointConnectionError,
        ) as exc:
            raise AttachmentStorageError(
                "Attachment storage "
                "healthcheck failed."
            ) from exc

        except Exception as exc:
            raise AttachmentStorageError(
                "Attachment storage "
                "healthcheck failed."
            ) from exc

        finally:
            try:
                self.client.delete_object(
                    Bucket=self.bucket,
                    Key=object_key,
                )

            except Exception:
                # Healthcheck cleanup is best-effort.
                pass


# =========================================================
# SINGLETON
# =========================================================


_storage: (
    AttachmentStorage | None
) = None


def get_attachment_storage(
) -> AttachmentStorage:
    global _storage

    if _storage is None:
        _storage = (
            AttachmentStorage()
        )

    return _storage


def reset_attachment_storage(
) -> None:
    """
    Clear the process-local attachment storage singleton.

    Intended for tests or configuration reload scenarios.
    """

    global _storage

    _storage = None


# =========================================================
# PUBLIC EXPORTS
# =========================================================


__all__ = [
    "AttachmentStorage",
    "AttachmentStorageError",
    "get_attachment_storage",
    "reset_attachment_storage",
]