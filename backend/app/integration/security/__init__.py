"""Integration security — tenant isolation, SSRF, permissions."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse

from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.integration.constants import INTEGRATION_PERMISSIONS
from app.models.user import User

ADMIN_ROLES = frozenset({"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "DXCON_ADMIN"})


def require_integration_permission(permission: str) -> tuple[User | None, tuple | None]:
    verify_jwt_in_request()
    user = User.query.get(get_jwt_identity())
    if not user or not user.is_active:
        return None, ({"error": "Unauthorized"}, 401)
    if user.role in ADMIN_ROLES:
        return user, None
    if permission == "INTEGRATION_VIEW":
        return user, None
    if user.role in {"LAB", "LAB_MANAGER", "LAB_TECHNICIAN"} and permission in {
        "CONNECTOR_MANAGE", "MAPPING_MANAGE", "MESSAGE_RETRY",
    }:
        return user, None
    return None, ({"error": "Forbidden", "code": "INTEGRATION_FORBIDDEN"}, 403)


def organization_scope() -> str | None:
    return getattr(g, "organization_id", None) or getattr(g, "tenant_organization_id", None)


def enforce_organization_access(user: User, organization_id: str) -> bool:
    if user.role in ADMIN_ROLES:
        return True
    return user.organization_id == organization_id


def validate_endpoint_url(url: str, *, production: bool = True) -> tuple[bool, str]:
    if not url:
        return False, "endpoint required"
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"}:
        return False, "unsupported scheme"
    if production and parsed.scheme != "https":
        return False, "HTTPS required in production"
    host = parsed.hostname or ""
    if not host:
        return False, "invalid host"
    if _is_private_host(host):
        return False, "private/internal endpoints blocked"
    return True, ""


def _is_private_host(host: str) -> bool:
    if host in {"localhost", "127.0.0.1", "0.0.0.0"}:
        return True
    if re.match(r"^10\.|^192\.168\.|^172\.(1[6-9]|2\d|3[0-1])\.", host):
        return True
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def mask_payload_preview(payload: str, limit: int = 500) -> str:
    masked = re.sub(r'"(password|token|secret|api_key|national_id)"\s*:\s*"[^"]*"', r'"\1":"***"', payload, flags=re.I)
    return masked[:limit]
