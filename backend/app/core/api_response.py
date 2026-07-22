from datetime import datetime, timezone

from flask import json, request

from app.core.request_context import get_correlation_id, get_request_id, get_trace_id


def utc_timestamp():
    return datetime.now(timezone.utc).isoformat()


def api_envelope(success, data=None, error=None):
    request_id = get_request_id() or "unknown"
    envelope = {
        "success": bool(success),
        "data": data,
        "error": error,
        "request_id": request_id,
        "timestamp": utc_timestamp(),
    }
    correlation_id = get_correlation_id()
    trace_id = get_trace_id()
    if correlation_id:
        envelope["correlation_id"] = correlation_id
    if trace_id:
        envelope["trace_id"] = trace_id
    return envelope


def success_response(data, status_code=200):
    return api_envelope(True, data=data, error=None), status_code


def error_response(code, message, status_code, field=None, details=None):
    error = {
        "code": code,
        "message": message,
        "request_id": get_request_id() or "unknown",
    }
    if field:
        error["field"] = field
    if details:
        error["details"] = details
    return api_envelope(False, data=None, error=error), status_code


def is_api_path(path=None):
    path = path or request.path
    return path.startswith("/api/")


def should_wrap_response(app, response):
    if app.config.get("TESTING"):
        return False
    if not app.config.get("API_RESPONSE_ENVELOPE", True):
        return False
    if not is_api_path():
        return False
    if response.status_code in {204, 304}:
        return False
    content_type = (response.content_type or "").lower()
    if "json" not in content_type:
        return False
    if response.direct_passthrough:
        return False
    return True


def init_api_response_envelope(app):
    @app.after_request
    def wrap_json_api_responses(response):
        if not should_wrap_response(app, response):
            return response

        try:
            payload = response.get_json(silent=True)
        except Exception:
            return response

        if payload is None:
            return response

        if isinstance(payload, dict) and "success" in payload:
            if "timestamp" not in payload:
                payload["timestamp"] = utc_timestamp()
                if "request_id" not in payload:
                    payload["request_id"] = get_request_id() or "unknown"
                response.set_data(json.dumps(payload))
                response.content_type = "application/json"
            return response

        # Preserve HTTP semantics: 4xx/5xx must not be wrapped as success=true.
        ok = 200 <= int(response.status_code) < 400
        if ok:
            wrapped = api_envelope(True, data=payload, error=None)
        else:
            if isinstance(payload, dict):
                message = str(
                    payload.get("error")
                    or payload.get("message")
                    or payload.get("detail")
                    or "Request failed"
                )
                code = str(payload.get("code") or ("UNAUTHORIZED" if response.status_code == 401 else "REQUEST_FAILED"))
                field = payload.get("field")
            else:
                message = str(payload)
                code = "REQUEST_FAILED"
                field = None
            error = {
                "code": code,
                "message": message,
                "request_id": get_request_id() or "unknown",
            }
            if field:
                error["field"] = field
            wrapped = api_envelope(False, data=None, error=error)

        response.set_data(json.dumps(wrapped))
        response.content_type = "application/json"
        return response
