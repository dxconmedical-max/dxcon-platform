"""Report logo helpers. Lookups never raise: no logo means the report renders without one."""

from __future__ import annotations

import base64

from flask import current_app
from sqlalchemy import inspect as sa_inspect

from app.extensions.db import db
from app.models.report_logo import ReportLogo
from app.storage.providers.local import LocalStorageProvider

MAX_LOGO_BYTES = 500 * 1024
OWNER_TYPES = {"DXCON", "LABORATORY", "PARTNER", "CLIENT"}
_PNG = b"\x89PNG\r\n\x1a\n"
_JPEG = b"\xff\xd8\xff"


def detect_logo_type(data: bytes) -> str | None:
    """Trust the bytes, not the file name. Only PNG/JPEG (SVG can carry scripts)."""
    if data.startswith(_PNG):
        return "image/png"
    if data.startswith(_JPEG):
        return "image/jpeg"
    return None


def _provider() -> LocalStorageProvider:
    return LocalStorageProvider(current_app.config.get("STORAGE_PATH", "uploads"))


def logo_data_uri(owner_type: str = "DXCON", owner_code: str = "") -> str | None:
    try:
        if not sa_inspect(db.engine).has_table("report_logos"):
            return None
        row = (
            ReportLogo.query.filter_by(owner_type=owner_type, owner_code=owner_code or "", is_active=True)
            .order_by(ReportLogo.created_at.desc())
            .first()
        )
        if not row:
            return None
        raw = _provider().get(row.storage_key)
        return f"data:{row.content_type};base64,{base64.b64encode(raw).decode('ascii')}"
    except Exception:
        return None


def logo_header_html(owner_type: str = "DXCON", owner_code: str = "") -> str:
    uri = logo_data_uri(owner_type, owner_code)
    if not uri:
        return ""
    return f'<div class="logo"><img src="{uri}" alt="Logo" style="max-height:60px;max-width:220px"></div>'
