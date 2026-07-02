"""Centralized application exceptions."""


class DxConError(Exception):
    """Base error for DxCon backend services."""

    def __init__(self, message, status_code=400, code=None, field=None, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.field = field
        self.details = details


class ApiError(DxConError):
    """API-facing error with HTTP status and stable error code."""


class ValidationError(ApiError):
    def __init__(self, message, field=None, details=None):
        super().__init__(message, status_code=422, code="UNPROCESSABLE_ENTITY", field=field, details=details)


class NotFoundError(ApiError):
    def __init__(self, message, field=None, details=None):
        super().__init__(message, status_code=404, code="NOT_FOUND", field=field, details=details)


class ConflictError(ApiError):
    def __init__(self, message, field=None, details=None):
        super().__init__(message, status_code=409, code="CONFLICT", field=field, details=details)


class AuthorizationError(ApiError):
    def __init__(self, message="Forbidden", field=None, details=None):
        super().__init__(message, status_code=403, code="FORBIDDEN", field=field, details=details)


class AuthenticationError(ApiError):
    def __init__(self, message="Unauthorized", field=None, details=None):
        super().__init__(message, status_code=401, code="UNAUTHORIZED", field=field, details=details)
