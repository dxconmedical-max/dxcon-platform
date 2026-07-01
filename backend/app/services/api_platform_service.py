import secrets
import time
import uuid

from app.core.passwords import hash_password, verify_password
from app.core.statuses import API_CLIENT_ACTIVE, API_KEY_ACTIVE, API_KEY_REVOKED
from app.extensions.db import db
from app.models.api_platform import ApiClient, ApiKey, ApiUsageLog


class ApiPlatformError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ApiClientService:
    @staticmethod
    def ensure_defaults():
        if ApiClient.query.first():
            return {"seeded": False}
        db.session.add(
            ApiClient(
                client_code="CLIENT-DEMO",
                name="Demo Partner",
                organization="Demo Hospital",
                contact_email="developer@demo.local",
                status=API_CLIENT_ACTIVE,
            )
        )
        db.session.commit()
        return {"seeded": True}

    @staticmethod
    def list_clients():
        rows = ApiClient.query.order_by(ApiClient.created_at.desc()).all()
        return {"count": len(rows), "clients": [row.to_dict() for row in rows]}

    @staticmethod
    def create(data):
        name = data.get("name")
        if not name:
            raise ApiPlatformError("name is required")
        client = ApiClient(
            client_code=data.get("client_code") or f"CLIENT-{uuid.uuid4().hex[:8].upper()}",
            name=name,
            organization=data.get("organization"),
            contact_email=data.get("contact_email"),
            status=API_CLIENT_ACTIVE,
        )
        db.session.add(client)
        db.session.commit()
        return client.to_dict()


class ApiKeyService:
    @staticmethod
    def list_keys(client_id=None):
        query = ApiKey.query
        if client_id:
            query = query.filter_by(client_id=client_id)
        rows = query.order_by(ApiKey.created_at.desc()).all()
        return {"count": len(rows), "keys": [row.to_dict() for row in rows]}

    @staticmethod
    def create(data):
        client_id = data.get("client_id")
        client = ApiClient.query.filter_by(id=client_id).first()
        if client is None:
            raise ApiPlatformError("client_id is required and must exist")
        raw_key = f"dxcon_{secrets.token_urlsafe(32)}"
        prefix = raw_key[:12]
        row = ApiKey(
            client_id=client.id,
            key_prefix=prefix,
            key_hash=hash_password(raw_key),
            status=API_KEY_ACTIVE,
        )
        db.session.add(row)
        db.session.commit()
        payload = row.to_dict()
        payload["api_key"] = raw_key
        payload["message"] = "Store this API key securely. It will not be shown again."
        return payload

    @staticmethod
    def revoke(key_id):
        row = ApiKey.query.filter_by(id=key_id).first()
        if row is None:
            raise ApiPlatformError("API key not found", 404)
        if row.status == API_KEY_REVOKED:
            return row.to_dict()
        row.status = API_KEY_REVOKED
        from datetime import datetime

        row.revoked_at = datetime.utcnow()
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def authenticate(raw_key: str):
        if not raw_key:
            return None
        prefix = raw_key[:12]
        candidates = ApiKey.query.filter_by(key_prefix=prefix, status=API_KEY_ACTIVE).all()
        for row in candidates:
            if verify_password(row.key_hash, raw_key):
                return row
        return None


class ApiUsageService:
    @staticmethod
    def log_usage(method, path, status_code, duration_ms=0, client_id=None, api_key_id=None):
        row = ApiUsageLog(
            client_id=client_id,
            api_key_id=api_key_id,
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def list_usage(client_id=None, limit=100):
        query = ApiUsageLog.query
        if client_id:
            query = query.filter_by(client_id=client_id)
        rows = query.order_by(ApiUsageLog.created_at.desc()).limit(min(limit, 200)).all()
        return {"count": len(rows), "usage": [row.to_dict() for row in rows]}


class ApiPlatformService:
    @staticmethod
    def inventory(app):
        from app.api_platform.api_inventory import scan_routes
        from app.api_platform.route_catalog import build_catalog

        scanned = scan_routes(app)
        catalog = build_catalog(scanned["routes"])
        return {
            "inventory": scanned,
            "catalog": catalog,
        }

    @staticmethod
    def health(app):
        from app.api_platform.versioning import version_info

        scanned = ApiPlatformService.inventory(app)["inventory"]
        return {
            "status": "OK" if scanned["summary"]["duplicate_count"] == 0 else "DEGRADED",
            "platform": "DxCon API Platform",
            "version": version_info(),
            "summary": scanned["summary"],
        }


class DeveloperSandboxService:
    ALLOWED_PREFIX = "/api/v1/"

    @staticmethod
    def execute(app, data):
        method = (data.get("method") or "GET").upper()
        path = data.get("path") or ""
        if not path.startswith(DeveloperSandboxService.ALLOWED_PREFIX):
            raise ApiPlatformError("Sandbox only allows /api/v1/ paths")
        if path.startswith("/api/v1/developer/sandbox/"):
            raise ApiPlatformError("Sandbox request endpoint cannot target itself")
        headers = data.get("headers") or {}
        payload = data.get("body")
        started = time.time()
        client = app.test_client()
        if method == "GET":
            response = client.get(path, headers=headers, query_string=data.get("query") or {})
        elif method == "POST":
            response = client.post(path, json=payload, headers=headers)
        elif method == "PUT":
            response = client.put(path, json=payload, headers=headers)
        elif method == "PATCH":
            response = client.patch(path, json=payload, headers=headers)
        elif method == "DELETE":
            response = client.delete(path, headers=headers)
        else:
            raise ApiPlatformError(f"Unsupported method: {method}")
        duration_ms = round((time.time() - started) * 1000, 2)
        raw_key = headers.get("X-API-Key") or headers.get("x-api-key")
        api_key = ApiKeyService.authenticate(raw_key) if raw_key else None
        usage = ApiUsageService.log_usage(
            method,
            path,
            response.status_code,
            duration_ms=duration_ms,
            client_id=api_key.client_id if api_key else None,
            api_key_id=api_key.id if api_key else None,
        )
        body = None
        if response.is_json:
            body = response.get_json()
        elif response.data:
            body = response.get_data(as_text=True)[:2000]
        return {
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "headers": dict(response.headers),
            "body": body,
            "usage_log_id": usage["id"],
        }
