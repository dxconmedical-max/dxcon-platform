from flask import request

from app.core.errors import ApiError


class ValidationError(ApiError):
    def __init__(self, message, field=None):
        super().__init__(message, status_code=422, code="VALIDATION_ERROR")
        self.field = field


def get_json_body():
    if request.method in {"GET", "DELETE", "HEAD", "OPTIONS"}:
        return {}

    if not request.is_json:
        raise ValidationError("Expected application/json content type")

    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("Malformed JSON payload")

    if not isinstance(data, dict):
        raise ValidationError("JSON body must be an object")

    return data


def require_fields(data, *fields):
    missing = [field for field in fields if data.get(field) in (None, "")]
    if missing:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing)}"
        )


def reject_unknown_fields(data, allowed_fields):
    unknown = sorted(set(data.keys()) - set(allowed_fields))
    if unknown:
        raise ValidationError(
            f"Unknown fields are not allowed: {', '.join(unknown)}"
        )


def validate_password(value, field="password", min_length=8):
    password = str(value or "")
    if len(password) < min_length:
        raise ValidationError(
            f"{field} must be at least {min_length} characters",
            field=field,
        )
    return password


def validate_email(value, field="email"):
    if not value or "@" not in str(value):
        raise ValidationError(f"Invalid {field}", field=field)
    return str(value).strip().lower()


def validate_role(value, allowed_roles, field="role"):
    role = str(value or "").upper()
    if role not in allowed_roles:
        raise ValidationError(f"Invalid {field}", field=field)
    return role
