"""Provision privileged users for smoke/go-live journeys.

Public ``/auth/register`` is PATIENT-only (P0 privilege escalation fix).
Staff/admin accounts used by validation scripts must be created in-process.
"""

from __future__ import annotations

from app.core.passwords import hash_password
from app.extensions.db import db
from app.models.user import User


def ensure_user(
    *,
    email: str,
    password: str,
    role: str = "ADMIN",
) -> User:
    user = User.query.filter_by(email=email).first()
    if user is None:
        user = User(
            email=email,
            role=role,
            password_hash=hash_password(password),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        return user

    user.role = role
    user.is_active = True
    user.password_hash = hash_password(password)
    db.session.add(user)
    db.session.commit()
    return user
