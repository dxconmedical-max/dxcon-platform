"""AI memory — Release 3.0 Epic 9."""

from __future__ import annotations

import uuid

from app.ai_platform.models import AIMemoryMessage, AIMemorySession
from app.ai_platform.phi_redaction import redact_phi
from app.extensions.db import db


class AIMemoryError(ValueError):
    pass


class AIMemoryService:
    @classmethod
    def create_session(cls, *, organization_id: str | None, user_id: str | None, context_type: str = "GENERAL") -> dict:
        row = AIMemorySession(
            session_code=f"MEM-{uuid.uuid4().hex[:8].upper()}",
            organization_id=organization_id,
            user_id=user_id,
            context_type=context_type,
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @classmethod
    def append_message(cls, session_id: str, role: str, content: str) -> dict:
        session = AIMemorySession.query.filter_by(id=session_id, status="ACTIVE").first()
        if not session:
            raise AIMemoryError("memory session not found")
        row = AIMemoryMessage(
            session_id=session_id,
            role=role.upper(),
            content_redacted=redact_phi(content),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @classmethod
    def get_session(cls, session_id: str) -> dict:
        session = AIMemorySession.query.filter_by(id=session_id).first()
        if not session:
            raise AIMemoryError("memory session not found")
        messages = (
            AIMemoryMessage.query.filter_by(session_id=session_id)
            .order_by(AIMemoryMessage.created_at.asc())
            .limit(50)
            .all()
        )
        return {**session.to_dict(), "messages": [m.to_dict() for m in messages]}
