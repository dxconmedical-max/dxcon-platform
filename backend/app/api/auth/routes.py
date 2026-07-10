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
from app.services.auth_context_service import (
    AuthContextError,
    build_capabilities,
    current_user_payload,
    list_user_memberships,
    switch_organization,
)
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


def _auth_context_error(exc: AuthContextError):
    return {"error": str(exc), "code": exc.code}, exc.status


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def auth_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return {"error": "Invalid user"}, 401
    return {"success": True, "data": current_user_payload(user)}, 200


@auth_bp.route("/memberships", methods=["GET"])
@jwt_required()
def auth_memberships():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return {"error": "Invalid user"}, 401
    return {
        "success": True,
        "data": list_user_memberships(user),
    }, 200


@auth_bp.route("/switch-organization", methods=["POST"])
@jwt_required()
def auth_switch_organization():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return {"error": "Invalid user"}, 401
    data = get_json_body()
    require_fields(data, "organization_id")
    organization_id = str(data.get("organization_id"))
    try:
        capabilities = switch_organization(user, organization_id)
        db.session.commit()
    except AuthContextError as exc:
        return _auth_context_error(exc)
    return {"success": True, "data": capabilities}, 200


@auth_bp.route("/capabilities", methods=["GET"])
@jwt_required()
def auth_capabilities():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return {"error": "Invalid user"}, 401
    organization_id = request.args.get("organization_id") or user.organization_id
    try:
        data = build_capabilities(user, organization_id)
    except AuthContextError as exc:
        return _auth_context_error(exc)
    return {"success": True, "data": data}, 200


@auth_bp.route("/forgot-password", methods=["POST"])
def auth_forgot_password():
    data = get_json_body()
    require_fields(data, "email")
    validate_email(data.get("email"))
    return {
        "success": True,
        "message": "If an account exists for this email, password reset instructions will be sent.",
    }, 200


@auth_bp.route("/reset-password", methods=["POST"])
def auth_reset_password():
    data = get_json_body()
    require_fields(data, "token", "password")
    validate_password(data.get("password"))
    return {
        "error": "Password reset is not yet enabled. Contact your administrator.",
        "code": "RESET_NOT_ENABLED",
    }, 501
