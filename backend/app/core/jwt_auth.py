from datetime import datetime

from flask_jwt_extended import get_jwt, verify_jwt_in_request

from app.core.errors import build_error_response
from app.extensions.jwt import jwt
from app.models.user import User
from app.services.refresh_token_service import RefreshTokenService


def init_jwt_security(app):
    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_payload):
        return build_error_response(
            "TOKEN_EXPIRED",
            "Token has expired",
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(_error):
        return build_error_response(
            "INVALID_TOKEN",
            "Invalid token",
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(_error):
        return build_error_response(
            "UNAUTHORIZED",
            "Authorization required",
            401,
        )

    @jwt.revoked_token_loader
    def revoked_token_callback(_jwt_header, _jwt_payload):
        return build_error_response(
            "TOKEN_REVOKED",
            "Token has been revoked",
            401,
        )

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_payload):
        if jwt_payload.get("type") != "refresh":
            return False
        return RefreshTokenService.is_revoked(jwt_payload.get("jti"))


def get_current_user():
    verify_jwt_in_request()
    claims = get_jwt()
    user_id = claims.get("sub")
    user = User.query.get(user_id)
    return user, claims


def require_active_user():
    user, claims = get_current_user()

    if not user:
        return build_error_response("UNAUTHORIZED", "User not found", 401)

    if not user.is_active:
        return build_error_response("FORBIDDEN", "User account is disabled", 403)

    token_exp = claims.get("exp")
    if token_exp and datetime.utcfromtimestamp(token_exp) < datetime.utcnow():
        return build_error_response("TOKEN_EXPIRED", "Token has expired", 401)

    return user, claims
