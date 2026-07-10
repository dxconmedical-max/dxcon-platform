from datetime import datetime
import uuid

from app.extensions.db import db


class AIProvider(db.Model):
    __tablename__ = "ai_platform_providers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    provider_type = db.Column(db.String(50), nullable=False, index=True)
    model_name = db.Column(db.String(100), default="local-advisory")
    config_json = db.Column(db.Text, default="{}")
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "provider_code": self.provider_code,
            "name": self.name,
            "provider_type": self.provider_type,
            "model_name": self.model_name,
            "config_json": self.config_json,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PromptTemplate(db.Model):
    __tablename__ = "ai_platform_prompts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt_code = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    task_type = db.Column(db.String(100), nullable=False, index=True)
    active_version = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "prompt_code": self.prompt_code,
            "name": self.name,
            "task_type": self.task_type,
            "active_version": self.active_version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PromptVersion(db.Model):
    __tablename__ = "ai_platform_prompt_versions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prompt_id = db.Column(db.String(36), db.ForeignKey("ai_platform_prompts.id"), nullable=False, index=True)
    version = db.Column(db.Integer, nullable=False)
    template_text = db.Column(db.Text, nullable=False)
    metadata_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "prompt_id": self.prompt_id,
            "version": self.version,
            "template_text": self.template_text,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIInferenceJob(db.Model):
    __tablename__ = "ai_platform_inference_jobs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_code = db.Column(db.String(50), unique=True, nullable=False)
    organization_id = db.Column(db.String(36), index=True)
    user_id = db.Column(db.String(36), index=True)
    session_id = db.Column(db.String(36), index=True)
    provider_id = db.Column(db.String(36), index=True)
    prompt_id = db.Column(db.String(36), index=True)
    prompt_version = db.Column(db.Integer)
    input_json = db.Column(db.Text, default="{}")
    output_json = db.Column(db.Text, default="{}")
    status = db.Column(db.String(50), default="QUEUED", index=True)
    human_review_required = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "job_code": self.job_code,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "provider_id": self.provider_id,
            "prompt_id": self.prompt_id,
            "prompt_version": self.prompt_version,
            "input_json": self.input_json,
            "output_json": self.output_json,
            "status": self.status,
            "human_review_required": bool(self.human_review_required),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class AIGovernancePolicy(db.Model):
    __tablename__ = "ai_platform_governance_policies"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), index=True)
    policy_code = db.Column(db.String(50), unique=True, nullable=False)
    advisory_only = db.Column(db.Boolean, default=True)
    phi_redaction_required = db.Column(db.Boolean, default=True)
    human_review_required = db.Column(db.Boolean, default=True)
    allowed_task_types_json = db.Column(db.Text, default='["interpretation","summary","general"]')
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "policy_code": self.policy_code,
            "advisory_only": bool(self.advisory_only),
            "phi_redaction_required": bool(self.phi_redaction_required),
            "human_review_required": bool(self.human_review_required),
            "allowed_task_types_json": self.allowed_task_types_json,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIMemorySession(db.Model):
    __tablename__ = "ai_platform_memory_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_code = db.Column(db.String(50), unique=True, nullable=False)
    organization_id = db.Column(db.String(36), index=True)
    user_id = db.Column(db.String(36), index=True)
    context_type = db.Column(db.String(50), default="GENERAL")
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "session_code": self.session_code,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "context_type": self.context_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AIMemoryMessage(db.Model):
    __tablename__ = "ai_platform_memory_messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey("ai_platform_memory_sessions.id"), nullable=False, index=True)
    role = db.Column(db.String(30), nullable=False)
    content_redacted = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content_redacted": self.content_redacted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIRagDocument(db.Model):
    __tablename__ = "ai_platform_rag_documents"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), index=True)
    document_code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    source_type = db.Column(db.String(50), default="KNOWLEDGE")
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "document_code": self.document_code,
            "title": self.title,
            "source_type": self.source_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIRagChunk(db.Model):
    __tablename__ = "ai_platform_rag_chunks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = db.Column(db.String(36), db.ForeignKey("ai_platform_rag_documents.id"), nullable=False, index=True)
    chunk_index = db.Column(db.Integer, default=0)
    content = db.Column(db.Text, nullable=False)
    token_estimate = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "token_estimate": self.token_estimate,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIAuditLog(db.Model):
    __tablename__ = "ai_platform_audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(100), nullable=False)
    resource_id = db.Column(db.String(100))
    actor = db.Column(db.String(255), default="SYSTEM")
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "actor": self.actor,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIUsageMetric(db.Model):
    __tablename__ = "ai_platform_usage_metrics"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_id = db.Column(db.String(36), index=True)
    task_type = db.Column(db.String(100), index=True)
    tokens_in = db.Column(db.Integer, default=0)
    tokens_out = db.Column(db.Integer, default=0)
    requests = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "task_type": self.task_type,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "requests": self.requests,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
