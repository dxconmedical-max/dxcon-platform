"""Resolve how an approver is displayed on a report (name, title, license)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import inspect as sa_inspect

from app.extensions.db import db
from app.models.staff_profile import StaffProfile  # noqa: F401  (registers the model)


def format_approver(email: str | None, profile: Any) -> str | None:
    if not email:
        return email
    if profile is None:
        return email
    name = (getattr(profile, "full_name", None) or "").strip()
    if not name:
        return email
    text = name
    title = (getattr(profile, "job_title", None) or "").strip()
    if title:
        text += f", {title}"
    license_no = (getattr(profile, "license_number", None) or "").strip()
    if license_no:
        text += f" (CCHN: {license_no})"
    return text


def describe_approver(email: str | None) -> str | None:
    """Never raises: falls back to the raw email when no profile/table/app context."""
    if not email:
        return email
    try:
        from app.models.user import User

        if not sa_inspect(db.engine).has_table("staff_profiles"):
            return email
        profile = (
            StaffProfile.query.join(User, User.id == StaffProfile.user_id)
            .filter(db.func.lower(User.email) == email.strip().lower(), StaffProfile.is_active.is_(True))
            .first()
        )
        return format_approver(email, profile)
    except Exception:
        return email
