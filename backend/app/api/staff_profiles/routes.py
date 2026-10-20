from flask import Blueprint, request

from app.core.authenticated_identity import blueprint_require_authenticated_user
from app.core.authz import require_platform_role
from app.core.errors import build_error_response
from app.extensions.db import db
from app.models.staff_profile import StaffProfile
from app.models.user import User

staff_profiles_bp = Blueprint(
    "staff_profiles",
    __name__,
    url_prefix="/api/v1/staff-profiles",
)
blueprint_require_authenticated_user(staff_profiles_bp)


def _row(user: User, profile: StaffProfile) -> dict:
    return {
        "email": user.email,
        "full_name": profile.full_name,
        "job_title": profile.job_title,
        "license_number": profile.license_number,
        "is_active": bool(profile.is_active),
    }


@staff_profiles_bp.route("", methods=["GET"])
@require_platform_role("SUPER_ADMIN")
def list_staff_profiles():
    rows = (
        db.session.query(User, StaffProfile)
        .join(StaffProfile, StaffProfile.user_id == User.id)
        .order_by(User.email)
        .all()
    )
    return {"count": len(rows), "profiles": [_row(u, p) for u, p in rows]}


@staff_profiles_bp.route("/<email>", methods=["PUT"])
@require_platform_role("SUPER_ADMIN")
def upsert_staff_profile(email: str):
    data = request.get_json(silent=True) or {}
    full_name = str(data.get("full_name") or "").strip()
    job_title = str(data.get("job_title") or "").strip() or None
    license_number = str(data.get("license_number") or "").strip() or None

    if not full_name:
        return build_error_response("VALIDATION_ERROR", "full_name is required", 422)
    if len(full_name) > 255 or (job_title and len(job_title) > 255) or (license_number and len(license_number) > 100):
        return build_error_response("VALIDATION_ERROR", "value too long", 422)

    user = User.query.filter(db.func.lower(User.email) == email.strip().lower()).first()
    if not user:
        return build_error_response("NOT_FOUND", "User not found", 404)

    profile = StaffProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = StaffProfile(user_id=user.id, full_name=full_name)
    profile.full_name = full_name
    profile.job_title = job_title
    profile.license_number = license_number
    if "is_active" in data:
        profile.is_active = bool(data.get("is_active"))
    db.session.add(profile)
    db.session.commit()
    return _row(user, profile), 200
