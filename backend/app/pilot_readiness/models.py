"""Pilot readiness models — Release 2.0 Epic 8."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.extensions.db import db

ONBOARDING_TYPES = (
    "LABORATORY",
    "CLINIC",
    "HOSPITAL",
    "DOCTOR",
    "COLLECTOR_COMPANY",
    "CORPORATE",
)

ONBOARDING_STEPS = (
    "organization",
    "verify_email",
    "verify_domain",
    "company_info",
    "address",
    "contact",
    "administrator",
    "subscription",
    "permissions",
    "activation",
)

PARTNER_REG_STATUSES = ("PENDING", "REVIEW", "APPROVED", "ACTIVATED", "REJECTED")

ORG_SETUP_STEPS = (
    "organization",
    "logo",
    "theme",
    "working_hours",
    "departments",
    "doctors",
    "collectors",
    "laboratories",
    "services",
    "finish",
)


class OnboardingSession(db.Model):
    __tablename__ = "pilot_onboarding_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_code = db.Column(db.String(50), unique=True, nullable=False)
    onboarding_type = db.Column(db.String(50), nullable=False)
    current_step = db.Column(db.String(50), default="organization")
    status = db.Column(db.String(50), default="IN_PROGRESS")
    organization_id = db.Column(db.String(36), index=True)
    payload_json = db.Column(db.Text)
    requester_email = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "session_code": self.session_code,
            "onboarding_type": self.onboarding_type,
            "current_step": self.current_step,
            "status": self.status,
            "organization_id": self.organization_id,
            "requester_email": self.requester_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class PartnerRegistration(db.Model):
    __tablename__ = "pilot_partner_registrations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    registration_code = db.Column(db.String(50), unique=True, nullable=False)
    partner_type = db.Column(db.String(50), nullable=False)
    organization_name = db.Column(db.String(255), nullable=False)
    contact_email = db.Column(db.String(255), nullable=False)
    contact_phone = db.Column(db.String(30))
    domain = db.Column(db.String(255))
    address = db.Column(db.Text)
    status = db.Column(db.String(50), default="PENDING")
    organization_id = db.Column(db.String(36))
    review_note = db.Column(db.Text)
    reviewed_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    activated_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "registration_code": self.registration_code,
            "partner_type": self.partner_type,
            "organization_name": self.organization_name,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "domain": self.domain,
            "address": self.address,
            "status": self.status,
            "organization_id": self.organization_id,
            "review_note": self.review_note,
            "reviewed_by": self.reviewed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
        }


class OrgSetupSession(db.Model):
    __tablename__ = "pilot_org_setup_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    current_step = db.Column(db.String(50), default="organization")
    status = db.Column(db.String(50), default="IN_PROGRESS")
    payload_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "current_step": self.current_step,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class KnowledgeArticle(db.Model):
    __tablename__ = "pilot_knowledge_articles"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    article_code = db.Column(db.String(50), unique=True, nullable=False)
    category = db.Column(db.String(50), default="FAQ")
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text)
    content_type = db.Column(db.String(30), default="ARTICLE")
    tags = db.Column(db.String(500))
    published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "article_code": self.article_code,
            "category": self.category,
            "title": self.title,
            "body": self.body,
            "content_type": self.content_type,
            "tags": self.tags,
            "published": self.published,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TrainingGuide(db.Model):
    __tablename__ = "pilot_training_guides"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guide_code = db.Column(db.String(50), unique=True, nullable=False)
    audience = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "guide_code": self.guide_code,
            "audience": self.audience,
            "title": self.title,
            "body": self.body,
            "sort_order": self.sort_order,
            "published": self.published,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PilotScorecardRun(db.Model):
    __tablename__ = "pilot_scorecard_runs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_code = db.Column(db.String(50), unique=True, nullable=False)
    score_pct = db.Column(db.Float, default=0)
    metrics_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "run_code": self.run_code,
            "score_pct": self.score_pct,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
