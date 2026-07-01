import json
import logging
import re
from datetime import datetime, timezone

SENSITIVE_KEYS = {
    "password",
    "token",
    "secret",
    "authorization",
    "api_key",
    "access_token",
    "refresh_token",
    "cookie",
    "jwt",
}


class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key.startswith("_") or key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
            }:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def redact_mapping(data):
    if not isinstance(data, dict):
        return data

    redacted = {}
    for key, value in data.items():
        if str(key).lower() in SENSITIVE_KEYS:
            redacted[key] = "[REDACTED]"
        elif isinstance(value, dict):
            redacted[key] = redact_mapping(value)
        else:
            redacted[key] = value
    return redacted


def sanitize_path(path):
    if not path or "?" not in path:
        return path

    base, query = path.split("?", 1)
    parts = []
    for segment in query.split("&"):
        if not segment:
            continue
        if "=" in segment:
            key, _value = segment.split("=", 1)
            if key.lower() in SENSITIVE_KEYS:
                parts.append(f"{key}=[REDACTED]")
            else:
                parts.append(segment)
        else:
            parts.append(segment)
    return f"{base}?{'&'.join(parts)}"


def configure_logging(app):
    level_name = app.config.get("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    log_format = (app.config.get("LOG_FORMAT") or "text").lower()

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)

    handler = logging.StreamHandler()
    handler.setLevel(level)

    if log_format == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] %(message)s"
            )
        )

    root_logger.addHandler(handler)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    app.logger.setLevel(level)
    if not app.logger.handlers:
        app.logger.addHandler(handler)

    return root_logger
