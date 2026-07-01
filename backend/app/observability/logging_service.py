import json
import logging
from datetime import datetime, timezone

from app.core.logging_config import SENSITIVE_KEYS
from app.core.request_context import get_correlation_id, get_request_id, get_trace_id, get_user_id


class StructuredLoggingService:
    logger = logging.getLogger("dxcon.observability")

    @staticmethod
    def sanitize(payload):
        if not isinstance(payload, dict):
            return payload
        cleaned = {}
        for key, value in payload.items():
            lowered = str(key).lower()
            if any(token in lowered for token in SENSITIVE_KEYS):
                cleaned[key] = "[REDACTED]"
            elif isinstance(value, dict):
                cleaned[key] = StructuredLoggingService.sanitize(value)
            else:
                cleaned[key] = value
        return cleaned

    @staticmethod
    def format_record(module, message, execution_ms=None, extra=None):
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "INFO",
            "module": module,
            "message": message,
            "request_id": get_request_id(),
            "correlation_id": get_correlation_id(),
            "trace_id": get_trace_id(),
            "user_id": get_user_id(),
            "execution_ms": execution_ms,
            "context": StructuredLoggingService.sanitize(extra or {}),
        }
        return record

    @staticmethod
    def log_event(module, message, execution_ms=None, extra=None):
        record = StructuredLoggingService.format_record(module, message, execution_ms, extra)
        StructuredLoggingService.logger.info(json.dumps(record, default=str))
        return record
