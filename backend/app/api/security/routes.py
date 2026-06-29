from app.core.audit import write_audit
from app.core.passwords import hash_password
from app.core.roles import ALL_ROLES
from app.core.validation import (
    get_json_body,
    require_fields,
    validate_email,
    validate_password,
    validate_role,
)
from app.extensions.db import db
from app.models.user import User

from flask import Blueprint

security_api_bp = Blueprint(
    "security_api",
    __name__,
    url_prefix="/api/v1/security"
)


@security_api_bp.route("/roles")
def roles():
    return {
        "roles": ALL_ROLES
    }


@security_api_bp.route("/users")
def users():
    items = User.query.all()

    return {
        "count": len(items),
        "users": [
            u.to_dict()
            for u in items
        ]
    }


@security_api_bp.route("/users", methods=["POST"])
def create_user():
    data = get_json_body()
    require_fields(data, "email", "password")

    email = validate_email(data.get("email"))
    password = validate_password(data.get("password"))
    phone = data.get("phone")
    role = validate_role(data.get("role", "PATIENT"), ALL_ROLES)

    existing = User.query.filter_by(
        email=email
    ).first()

    if existing:
        return {"error": "user already exists"}, 409

    user = User(
        email=email,
        phone=phone,
        password_hash=hash_password(password),
        role=role,
        is_active=True
    )

    db.session.add(user)
    write_audit(
        action="CREATE_USER",
        object_type="USER",
        object_id=user.id,
        user_email="ADMIN"
    )
    db.session.commit()

    return {
        "success": True,
        "user": user.to_dict()
    }, 201


@security_api_bp.route("/users/<user_id>/role", methods=["POST"])
def update_role(user_id):
    data = get_json_body()
    require_fields(data, "role")
    role = validate_role(data.get("role"), ALL_ROLES)

    user = User.query.get(user_id)

    if not user:
        return {"error": "user not found"}, 404

    user.role = role
    write_audit(
        action="CHANGE_ROLE",
        object_type="USER",
        object_id=user.id,
        user_email="ADMIN"
    )
    db.session.commit()

    return {
        "success": True,
        "user": user.to_dict()
    }


@security_api_bp.route("/users/<user_id>/disable", methods=["POST", "GET"])
def disable_user(user_id):

    user = User.query.get(user_id)

    if not user:
        return {"error": "user not found"}, 404

    user.is_active = False
    db.session.commit()

    return {
        "success": True,
        "user": user.to_dict()
    }
