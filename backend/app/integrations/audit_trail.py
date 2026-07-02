import json

from app.extensions.db import db
from app.integrations.models import IntegrationPlatformAuditLog


class IntegrationAuditTrail:
    @staticmethod
    def write(action, resource_type, resource_id=None, detail=None, actor="SYSTEM"):
        row = IntegrationPlatformAuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor=actor,
            detail_json=json.dumps(detail or {}),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def list_entries(action=None, resource_type=None, page=1, page_size=50):
        page = max(int(page or 1), 1)
        page_size = min(max(int(page_size or 50), 1), 200)
        query = IntegrationPlatformAuditLog.query
        if action:
            query = query.filter_by(action=action)
        if resource_type:
            query = query.filter_by(resource_type=resource_type)
        total = query.count()
        rows = (
            query.order_by(IntegrationPlatformAuditLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"count": total, "entries": [row.to_dict() for row in rows]}
