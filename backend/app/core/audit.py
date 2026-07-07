from app.extensions.db import db
from app.models.audit_log import AuditLog
from datetime import datetime
import uuid

_COLUMN_CACHE: dict[str, bool] = {}

def table_has_column(table: str, column: str) -> bool:
    """Public helper for safe column-existence checks.

    Use this instead of importing the private `_table_has_column` across modules.
    """
    return _table_has_column(table, column)


def _table_has_column(table: str, column: str) -> bool:
    """Check column existence using the active session connection (safe for sqlite :memory:)."""
    key = f"{table}.{column}"
    if key in _COLUMN_CACHE:
        return _COLUMN_CACHE[key]
    try:
        bind = db.session.get_bind()
        if bind.dialect.name == "sqlite":
            rows = db.session.execute(db.text(f"PRAGMA table_info({table})")).fetchall()
            found = any(row[1] == column for row in rows)
        else:
            found = (
                db.session.execute(
                    db.text(
                        "SELECT 1 FROM information_schema.columns "
                        "WHERE table_name = :table AND column_name = :column LIMIT 1"
                    ),
                    {"table": table, "column": column},
                ).first()
                is not None
            )
        _COLUMN_CACHE[key] = found
        return found
    except Exception:
        _COLUMN_CACHE[key] = False
        return False


def _current_request_id():
    try:
        from flask import g, has_request_context, request

        if has_request_context():
            if getattr(g, "request_id", None):
                return g.request_id
            header_name = "X-Request-ID"
            return request.headers.get(header_name)
    except RuntimeError:
        pass
    return None


def write_audit(
    action,
    object_type,
    object_id,
    user_email="SYSTEM",
    ip_address="",
    request_id=None,
):
    audit_id = str(uuid.uuid4())
    created_at = datetime.utcnow()
    if _table_has_column("audit_logs", "request_id"):
        log = AuditLog(
            user_email=user_email,
            action=action,
            object_type=object_type,
            object_id=str(object_id),
            ip_address=ip_address,
            request_id=request_id or _current_request_id(),
        )
        db.session.add(log)
        return log

    db.session.execute(
        db.text(
            "INSERT INTO audit_logs (id, user_email, action, object_type, object_id, ip_address, created_at) "
            "VALUES (:id, :user_email, :action, :object_type, :object_id, :ip_address, :created_at)"
        ),
        {
            "id": audit_id,
            "user_email": user_email,
            "action": action,
            "object_type": object_type,
            "object_id": str(object_id),
            "ip_address": ip_address,
            "created_at": created_at,
        },
    )
    return AuditLog(
        id=audit_id,
        user_email=user_email,
        action=action,
        object_type=object_type,
        object_id=str(object_id),
        ip_address=ip_address,
        created_at=created_at,
    )
