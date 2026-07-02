"""S3-compatible and MinIO storage providers."""

from __future__ import annotations

from app.storage.providers.base import StorageProvider, StoredObject
from app.storage.providers.local import LocalStorageProvider


class S3StorageProvider(StorageProvider):
    name = "s3"

    def __init__(self, *, bucket: str, region: str, access_key: str, secret_key: str, endpoint_url: str | None = None):
        self.bucket = bucket
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.endpoint_url = endpoint_url
        self._fallback = LocalStorageProvider(f"/tmp/dxcon-s3-{bucket}")

    def _client(self):
        import boto3

        return boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            endpoint_url=self.endpoint_url,
        )

    @property
    def available(self) -> bool:
        try:
            import boto3  # noqa: F401

            return bool(self.bucket and self.access_key and self.secret_key)
        except ImportError:
            return False

    def put(self, key: str, data: bytes, content_type: str) -> StoredObject:
        if not self.available:
            return self._fallback.put(key, data, content_type)
        client = self._client()
        client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        return StoredObject(key=key, size_bytes=len(data), content_type=content_type, provider=self.name)

    def get(self, key: str) -> bytes:
        if not self.available:
            return self._fallback.get(key)
        response = self._client().get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def delete(self, key: str) -> bool:
        if not self.available:
            return self._fallback.delete(key)
        self._client().delete_object(Bucket=self.bucket, Key=key)
        return True

    def exists(self, key: str) -> bool:
        if not self.available:
            return self._fallback.exists(key)
        try:
            self._client().head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def validate_config(self) -> dict:
        missing = [name for name, value in (
            ("S3_BUCKET", self.bucket),
            ("S3_ACCESS_KEY", self.access_key),
            ("S3_SECRET_KEY", self.secret_key),
            ("S3_REGION", self.region),
        ) if not value]
        return {
            "ok": not missing,
            "missing": missing,
            "bucket": self.bucket,
            "region": self.region,
            "endpoint_url": self.endpoint_url,
            "client_available": self.available,
        }


class MinIOStorageProvider(S3StorageProvider):
    name = "minio"

    def __init__(self, *, bucket: str, access_key: str, secret_key: str, endpoint_url: str, region: str = "us-east-1"):
        super().__init__(
            bucket=bucket,
            region=region,
            access_key=access_key,
            secret_key=secret_key,
            endpoint_url=endpoint_url,
        )

    def validate_config(self) -> dict:
        payload = super().validate_config()
        payload["ok"] = payload["ok"] and bool(self.endpoint_url)
        if not self.endpoint_url:
            payload.setdefault("missing", []).append("S3_ENDPOINT_URL")
        payload["minio"] = True
        return payload
