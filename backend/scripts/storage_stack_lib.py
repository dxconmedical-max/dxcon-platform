"""Storage stack validation helpers."""

from __future__ import annotations

import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent

STORAGE_FILES = (
    "app/storage/factory.py",
    "app/storage/models.py",
    "app/storage/attachment_service.py",
    "app/storage/signed_urls.py",
    "app/storage/validation.py",
    "app/storage/lifecycle.py",
    "app/storage/virus_scan.py",
    "app/storage/metrics.py",
    "app/storage/providers/local.py",
    "app/storage/providers/s3.py",
    "app/api/files/routes.py",
)

FILE_ENDPOINTS = (
    "/api/v1/files",
    "/api/v1/files/upload",
    "/api/v1/system/storage",
)


def find_duplicate_routes(app):
    seen = defaultdict(list)
    for rule in app.url_map.iter_rules():
        methods = sorted(m for m in rule.methods if m not in {"HEAD", "OPTIONS"})
        key = (str(rule.rule), tuple(methods))
        seen[key].append(rule.endpoint)
    return {str(key): endpoints for key, endpoints in seen.items() if len(endpoints) > 1}


def verify_storage_modules() -> dict:
    missing = [path for path in STORAGE_FILES if not (ROOT / path).exists()]
    return {"ok": not missing, "missing": missing}


def verify_provider_configs(app) -> dict:
    from app.storage.providers.local import LocalStorageProvider
    from app.storage.providers.s3 import MinIOStorageProvider, S3StorageProvider

    local = LocalStorageProvider(app.config.get("STORAGE_PATH", "uploads"))
    s3 = S3StorageProvider(
        bucket=app.config.get("S3_BUCKET") or "dxcon-staging",
        region=app.config.get("S3_REGION") or "us-east-1",
        access_key=app.config.get("S3_ACCESS_KEY") or "access-key",
        secret_key=app.config.get("S3_SECRET_KEY") or "secret-key",
        endpoint_url=app.config.get("S3_ENDPOINT_URL") or None,
    )
    minio = MinIOStorageProvider(
        bucket=app.config.get("S3_BUCKET") or "dxcon-staging",
        access_key=app.config.get("S3_ACCESS_KEY") or "minio",
        secret_key=app.config.get("S3_SECRET_KEY") or "minio123",
        endpoint_url=app.config.get("S3_ENDPOINT_URL") or "http://minio:9000",
    )
    return {
        "ok": local.validate_config()["ok"] and s3.validate_config()["ok"] and minio.validate_config()["ok"],
        "local": local.validate_config(),
        "s3": s3.validate_config(),
        "minio": minio.validate_config(),
    }


def verify_file_endpoints(app) -> dict:
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    missing = [path for path in FILE_ENDPOINTS if path not in routes]
    dynamic = any("/api/v1/files/<file_id>" in route for route in routes)
    return {"ok": not missing and dynamic, "missing": missing, "dynamic_routes": dynamic}


def run_storage_smoke(app) -> dict:
    from io import BytesIO

    client = app.test_client()
    with tempfile.TemporaryDirectory() as tmp:
        app.config["STORAGE_PATH"] = tmp
        app.config["STORAGE_PROVIDER"] = "local"
        from app.storage.factory import init_storage_platform

        init_storage_platform(app)
        steps = {}
        upload = client.post(
            "/api/v1/files/upload",
            data={"file": (BytesIO(b"hello storage"), "report.pdf"), "tenant_id": "TEN-001"},
            content_type="multipart/form-data",
        )
        steps["upload"] = upload.status_code == 201
        payload = upload.get_json() or {}
        file_id = payload.get("id")
        steps["metadata_saved"] = bool(file_id) and payload.get("checksum_sha256")
        get_resp = client.get(f"/api/v1/files/{file_id}")
        steps["get_metadata"] = get_resp.status_code == 200
        signed = client.post(f"/api/v1/files/{file_id}/signed-url")
        signed_payload = signed.get_json() or {}
        steps["signed_url"] = signed.status_code == 200 and "signed_url" in signed_payload
        signed_url = signed_payload.get("signed_url", {}).get("url", "")
        download = client.get(signed_url)
        steps["download"] = download.status_code == 200 and download.data == b"hello storage"
        storage = client.get("/api/v1/system/storage")
        storage_payload = storage.get_json() or {}
        steps["storage_metrics"] = storage.status_code == 200 and storage_payload.get("metrics", {}).get("files_total", 0) >= 1
    passed = sum(1 for ok in steps.values() if ok)
    return {"ok": passed == len(steps), "passed": passed, "total": len(steps), "steps": steps}


def run_storage_stack_verification() -> dict:
    import os

    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
    from app import create_app
    from app.extensions.db import db

    app = create_app()
    app.config["TESTING"] = True
    with app.app_context():
        db.create_all()
        checks = {
            "storage_modules": verify_storage_modules(),
            "provider_configs": verify_provider_configs(app),
            "file_endpoints": verify_file_endpoints(app),
            "route_inventory": {"ok": not find_duplicate_routes(app), "count": len(find_duplicate_routes(app))},
            "storage_smoke": run_storage_smoke(app),
        }
    passed = sum(1 for item in checks.values() if item.get("ok"))
    return {"ok": passed == len(checks), "passed": passed, "total": len(checks), "checks": checks}
