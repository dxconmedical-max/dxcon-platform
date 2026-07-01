from datetime import datetime

from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

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
from app.services.refresh_token_service import RefreshTokenService

from app.core.passwords import (
    hash_password,
    verify_password,
)

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/v1/auth",
)


def _issue_tokens(user):
    additional_claims = {
        "role": user.role,
        "email": user.email,
    }

    access_token = create_access_token(
        identity=user.id,
        additional_claims=additional_claims,
    )
    refresh_token = create_refresh_token(
        identity=user.id,
        additional_claims=additional_claims,
    )

    decoded = decode_token(refresh_token)
    RefreshTokenService.register(
        user_id=user.id,
        jti=decoded["jti"],
        expires_at=datetime.utcfromtimestamp(decoded["exp"]),
    )

    return access_token, refresh_token


@auth_bp.route("/register", methods=["POST"])
def register():
    data = get_json_body()
    require_fields(data, "email", "password")

    email = validate_email(data.get("email"))
    password = validate_password(data.get("password"))
    phone = data.get("phone")
    role = validate_role(data.get("role", "PATIENT"), ALL_ROLES)

    existing_user = User.query.filter_by(
        email=email,
    ).first()

    if existing_user:
        return {
            "error": "Email already exists",
        }, 400

    user = User(
        email=email,
        phone=phone,
        role=role,
        password_hash=hash_password(password),
    )

    db.session.add(user)
    db.session.commit()

    return {
        "message": "User created successfully",
        "role": role,
    }, 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = get_json_body()
    require_fields(data, "email", "password")

    email = validate_email(data.get("email"))
    password = validate_password(data.get("password"))

    user = User.query.filter_by(
        email=email,
    ).first()

    if not user:
        return {
            "error": "Invalid credentials",
        }, 401

    if not user.is_active:
        return {
            "error": "Account disabled",
        }, 403

    if not verify_password(
        user.password_hash,
        password,
    ):
        return {
            "error": "Invalid credentials",
        }, 401

    access_token, refresh_token = _issue_tokens(user)
    db.session.commit()

    return {
        "success": True,
        "token": access_token,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "email": user.email,
        "role": user.role,
        "user": user.to_dict(),
    }


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.is_active:
        return {
            "error": "Invalid user",
        }, 401

    claims = get_jwt()
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            "role": user.role,
            "email": user.email,
        },
    )

    return {
        "success": True,
        "token": access_token,
        "access_token": access_token,
        "refresh_token_claims": {
            "type": claims.get("type"),
            "exp": claims.get("exp"),
        },
    }


@auth_bp.route("/logout", methods=["POST"])
@jwt_required(refresh=True)
def logout():
    claims = get_jwt()
    RefreshTokenService.revoke(claims.get("jti"))
    db.session.commit()

    return {
        "success": True,
        "message": "Logged out",
    }
