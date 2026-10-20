import uuid

from flask import Blueprint, request

from app.core.authenticated_identity import blueprint_require_authenticated_user
from app.core.authz import require_platform_role
from app.core.errors import build_error_response
from app.extensions.db import db
from app.models.report_logo import ReportLogo
from app.reporting_engine.logos import MAX_LOGO_BYTES, OWNER_TYPES, _provider, detect_logo_type

report_logos_bp = Blueprint("report_logos", __name__, url_prefix="/api/v1/report-logos")
blueprint_require_authenticated_user(report_logos_bp)


def _row(r: ReportLogo) -> dict:
    return {
        "id": r.id,
        "owner_type": r.owner_type,
        "owner_code": r.owner_code,
        "display_name": r.display_name,
        "content_type": r.content_type,
        "size_bytes": r.size_bytes,
        "is_active": bool(r.is_active),
    }


@report_logos_bp.route("", methods=["GET"])
@require_platform_role("SUPER_ADMIN")
def list_logos():
    rows = ReportLogo.query.order_by(ReportLogo.created_at.desc()).all()
    return {"count": len(rows), "logos": [_row(r) for r in rows]}


@report_logos_bp.route("", methods=["POST"])
@require_platform_role("SUPER_ADMIN")
def upload_logo():
    owner_type = str(request.form.get("owner_type", "")).strip().upper()
    owner_code = str(request.form.get("owner_code", "")).strip()[:100]
    display_name = str(request.form.get("display_name", "")).strip()[:255]
    upload = request.files.get("file")
    if owner_type not in OWNER_TYPES:
        return build_error_response("VALIDATION_ERROR", "owner_type must be one of " + ", ".join(sorted(OWNER_TYPES)), 422)
    if not display_name or upload is None:
        return build_error_response("VALIDATION_ERROR", "display_name and file are required", 422)
    data = upload.read(MAX_LOGO_BYTES + 1)
    if len(data) > MAX_LOGO_BYTES:
        return build_error_response("VALIDATION_ERROR", "logo larger than 500 KB", 422)
    content_type = detect_logo_type(data)
    if not content_type:
        return build_error_response("VALIDATION_ERROR", "only PNG or JPEG images are accepted", 422)
    ext = "png" if content_type == "image/png" else "jpg"
    key = f"logos/{uuid.uuid4()}.{ext}"
    _provider().put(key, data, content_type)
    row = ReportLogo(
        owner_type=owner_type, owner_code=owner_code, display_name=display_name,
        storage_key=key, content_type=content_type, size_bytes=len(data),
    )
    db.session.add(row)
    db.session.commit()
    return _row(row), 201


@report_logos_bp.route("/<logo_id>", methods=["PATCH"])
@require_platform_role("SUPER_ADMIN")
def toggle_logo(logo_id: str):
    row = db.session.get(ReportLogo, logo_id)
    if not row:
        return build_error_response("NOT_FOUND", "Logo not found", 404)
    data = request.get_json(silent=True) or {}
    if "is_active" in data:
        row.is_active = bool(data["is_active"])
        db.session.commit()
    return _row(row), 200


@report_logos_bp.route("/<logo_id>", methods=["DELETE"])
@require_platform_role("SUPER_ADMIN")
def delete_logo(logo_id: str):
    row = db.session.get(ReportLogo, logo_id)
    if not row:
        return build_error_response("NOT_FOUND", "Logo not found", 404)
    try:
        _provider().delete(row.storage_key)
    except Exception:
        pass
    db.session.delete(row)
    db.session.commit()
    return {"deleted": logo_id}, 200
