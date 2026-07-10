"""AI governance — Release 3.0 Epic 9."""

from __future__ import annotations

import json
import uuid

from app.ai_platform.models import AIGovernancePolicy
from app.extensions.db import db

DEFAULT_TASK_TYPES = ("interpretation", "summary", "risk", "reference_range", "patient_friendly", "general")


class AIGovernanceService:
    @classmethod
    def ensure_default_policy(cls, organization_id: str | None = None) -> dict:
        code = f"GOV-{(organization_id or 'GLOBAL')[:8].upper()}"
        row = AIGovernancePolicy.query.filter_by(policy_code=code).first()
        if row:
            return row.to_dict()
        row = AIGovernancePolicy(
            policy_code=code,
            organization_id=organization_id,
            allowed_task_types_json=json.dumps(list(DEFAULT_TASK_TYPES)),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @classmethod
    def evaluate_request(cls, task_type: str, organization_id: str | None = None) -> dict:
        policy = cls.ensure_default_policy(organization_id)
        allowed = json.loads(policy.get("allowed_task_types_json") or "[]")
        if task_type not in allowed:
            return {
                "allowed": False,
                "message": f"Task type '{task_type}' not permitted by governance policy",
                "policy": policy,
            }
        return {
            "allowed": True,
            "advisory_only": policy.get("advisory_only", True),
            "phi_redaction_required": policy.get("phi_redaction_required", True),
            "human_review_required": policy.get("human_review_required", True),
            "policy": policy,
        }

    @classmethod
    def list_policies(cls) -> dict:
        rows = AIGovernancePolicy.query.order_by(AIGovernancePolicy.created_at.desc()).all()
        return {"count": len(rows), "policies": [r.to_dict() for r in rows]}

    @classmethod
    def upsert_policy(cls, data: dict) -> dict:
        org_id = data.get("organization_id")
        code = data.get("policy_code") or f"GOV-{uuid.uuid4().hex[:8].upper()}"
        row = AIGovernancePolicy.query.filter_by(policy_code=code).first()
        if not row:
            row = AIGovernancePolicy(policy_code=code, organization_id=org_id)
            db.session.add(row)
        if "allowed_task_types" in data:
            row.allowed_task_types_json = json.dumps(data["allowed_task_types"])
        for field in ("advisory_only", "phi_redaction_required", "human_review_required", "status"):
            if field in data:
                setattr(row, field, data[field])
        db.session.commit()
        return row.to_dict()
