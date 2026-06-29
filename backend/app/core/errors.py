import logging

from flask import request
from werkzeug.exceptions import HTTPException

from app.core.request_context import get_request_id

logger = logging.getLogger("dxcon.errors")

STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "UNPROCESSABLE_ENTITY",
    413: "PAYLOAD_TOO_LARGE",
    429: "RATE_LIMIT_EXCEEDED",
    500: "INTERNAL_SERVER_ERROR",
}


class ApiError(Exception):
    def __init__(self, message, status_code=400, code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code or STATUS_CODES.get(status_code, "API_ERROR")


def is_api_request():
    return request.path.startswith("/api/")


def build_error_response(code, message, status_code):
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "request_id": get_request_id() or "unknown",
        },
    }, status_code


def register_error_handlers(app):
    for status_code, code in STATUS_CODES.items():

        def _handler(error, status_code=status_code, code=code):
            if not is_api_request():
                return error

            message = getattr(error, "description", None) or str(error)
            return build_error_response(code, message, status_code)

        app.register_error_handler(status_code, _handler)

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return build_error_response(error.code, error.message, error.status_code)

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        if not is_api_request():
            return error

        status_code = error.code or 500
        code = STATUS_CODES.get(status_code, "HTTP_ERROR")
        message = error.description or error.name
        return build_error_response(code, message, status_code)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        logger.exception(
            "Unhandled exception",
            extra={"request_id": get_request_id()},
        )

        if not is_api_request():
            raise error

        return build_error_response(
            STATUS_CODES[500],
            "An unexpected error occurred",
            500,
        )
