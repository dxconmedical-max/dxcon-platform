import hashlib
import json
import secrets
from datetime import datetime, timedelta

from flask import current_app

from app.extensions.db import db
from app.integrations.audit_trail import IntegrationAuditTrail
from app.integrations.models import PartnerSandboxToken


class SandboxTokenService:
    @staticmethod
    def _hash_token(token):
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def issue(partner_id, scopes=None, ttl_seconds=None):
        ttl = ttl_seconds or current_app.config.get("SANDBOX_TOKEN_TTL_SECONDS", 3600)
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(seconds=int(ttl))
        row = PartnerSandboxToken(
            partner_id=partner_id,
            token_hash=SandboxTokenService._hash_token(token),
            scopes_json=json.dumps(scopes or ["integrations:read", "integrations:write"]),
            expires_at=expires_at,
        )
        db.session.add(row)
        db.session.commit()
        IntegrationAuditTrail.write(
            action="SANDBOX_TOKEN_ISSUED",
            resource_type="PartnerSandboxToken",
            resource_id=row.id,
            detail={"partner_id": partner_id, "expires_at": expires_at.isoformat()},
        )
        return {
            "token": token,
            "partner_id": partner_id,
            "expires_at": expires_at.isoformat(),
            "scopes": scopes or ["integrations:read", "integrations:write"],
        }

    @staticmethod
    def validate(token):
        token_hash = SandboxTokenService._hash_token(token)
        row = PartnerSandboxToken.query.filter_by(token_hash=token_hash).first()
        if row is None:
            return {"valid": False, "reason": "not_found"}
        if row.expires_at and row.expires_at < datetime.utcnow():
            return {"valid": False, "reason": "expired"}
        return {"valid": True, "partner_id": row.partner_id, "scopes": row.scopes_json}
