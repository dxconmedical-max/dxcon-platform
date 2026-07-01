import logging
import time
import uuid

from flask import g, request

from app.core.logging_config import sanitize_path
from app.core.metrics import metrics

logger = logging.getLogger("dxcon.request")


def get_request_id():
    return getattr(g, "request_id", None) if g else None


def get_user_id():
    return getattr(g, "user_id", None) if g else None


def get_correlation_id():
    return getattr(g, "correlation_id", None) if g else None


def get_trace_id():
    return getattr(g, "trace_id", None) if g else None


def get_tenant_id():
    return getattr(g, "tenant_id", None) if g else None


def _resolve_user_id():
    user_id = request.headers.get("X-User-Id")
    if user_id:
        return user_id

    user_email = request.headers.get("X-User-Email")
    if user_email:
        return user_email

    try:
        from flask import session

        session_user_id = session.get("user_id")
        if session_user_id:
            return str(session_user_id)
    except RuntimeError:
        pass

    return None


def init_request_context(app):
    header_name = app.config.get("REQUEST_ID_HEADER", "X-Request-ID")
    correlation_header = app.config.get("CORRELATION_ID_HEADER", "X-Correlation-ID")
    trace_header = app.config.get("TRACE_ID_HEADER", "X-Trace-ID")
    tenant_header = app.config.get("TENANT_ID_HEADER", "X-Tenant-ID")

    @app.before_request
    def assign_request_context():
        incoming = request.headers.get(header_name)
        g.request_id = incoming or str(uuid.uuid4())
        g.correlation_id = request.headers.get(correlation_header) or g.request_id
        g.trace_id = request.headers.get(trace_header) or g.correlation_id
        g.tenant_id = request.headers.get(tenant_header)
        g.request_start_time = time.perf_counter()
        g.user_id = _resolve_user_id()

    @app.after_request
    def log_and_measure_request(response):
        started = getattr(g, "request_start_time", None)
        duration_ms = (
            round((time.perf_counter() - started) * 1000, 2)
            if started is not None
            else 0.0
        )

        metrics.record_request(duration_ms)
        if response.status_code >= 400:
            metrics.record_error()

        response.headers[header_name] = getattr(g, "request_id", "unknown")
        response.headers[correlation_header] = getattr(g, "correlation_id", "unknown")
        response.headers[trace_header] = getattr(g, "trace_id", "unknown")

        log_payload = {
            "request_id": getattr(g, "request_id", "unknown"),
            "correlation_id": getattr(g, "correlation_id", "unknown"),
            "trace_id": getattr(g, "trace_id", "unknown"),
            "method": request.method,
            "path": sanitize_path(request.full_path.rstrip("?")),
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "user_id": getattr(g, "user_id", None),
            "tenant_id": getattr(g, "tenant_id", None),
        }

        log_format = (app.config.get("LOG_FORMAT") or "text").lower()
        if log_format == "json":
            logger.info("request completed", extra=log_payload)
        else:
            logger.info(
                "request_id=%s trace_id=%s method=%s path=%s status=%s duration_ms=%s user_id=%s tenant_id=%s",
                log_payload["request_id"],
                log_payload["trace_id"],
                log_payload["method"],
                log_payload["path"],
                log_payload["status_code"],
                log_payload["duration_ms"],
                log_payload["user_id"] or "-",
                log_payload["tenant_id"] or "-",
            )

        return response
