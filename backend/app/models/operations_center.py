"""Operations Center models — Release 1.0 Operations Excellence.

Additive tables for support tickets and customer requests used by the
Operations Center dashboard and customer success workflows.
"""

from datetime import datetime
import uuid

from app.extensions.db import db


class SupportTicket(db.Model):
    __tablename__ = "opsc_support_tickets"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_code = db.Column(db.String(50), unique=True, nullable=False)
    organization_id = db.Column(db.String(36), index=True)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default="GENERAL")
    priority = db.Column(db.String(30), default="NORMAL")
    status = db.Column(db.String(50), default="OPEN")
    requester_email = db.Column(db.String(255))
    assigned_to = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "ticket_code": self.ticket_code,
            "organization_id": self.organization_id,
            "subject": self.subject,
            "description": self.description,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "requester_email": self.requester_email,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class CustomerRequest(db.Model):
    __tablename__ = "opsc_customer_requests"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_code = db.Column(db.String(50), unique=True, nullable=False)
    organization_id = db.Column(db.String(36), index=True)
    request_type = db.Column(db.String(50), default="FEATURE")
    title = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text)
    status = db.Column(db.String(50), default="PENDING")
    priority = db.Column(db.String(30), default="NORMAL")
    requested_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "request_code": self.request_code,
            "organization_id": self.organization_id,
            "request_type": self.request_type,
            "title": self.title,
            "details": self.details,
            "status": self.status,
            "priority": self.priority,
            "requested_by": self.requested_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
