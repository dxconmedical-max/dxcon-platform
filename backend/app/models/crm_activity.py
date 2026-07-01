from datetime import datetime
import uuid

from app.extensions.db import db


class Activity(db.Model):
    __tablename__ = "crm_activities"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    activity_type = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    related_type = db.Column(db.String(50))
    related_id = db.Column(db.String(36))
    lead_id = db.Column(db.String(36), db.ForeignKey("crm_leads.id"))
    customer_id = db.Column(db.String(36), db.ForeignKey("crm_customers.id"))
    opportunity_id = db.Column(db.String(36), db.ForeignKey("crm_opportunities.id"))
    due_date = db.Column(db.DateTime)
    reminder_at = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    attachment_url = db.Column(db.String(500))
    owner = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "activity_type": self.activity_type,
            "subject": self.subject,
            "description": self.description,
            "related_type": self.related_type,
            "related_id": self.related_id,
            "lead_id": self.lead_id,
            "customer_id": self.customer_id,
            "opportunity_id": self.opportunity_id,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "reminder_at": self.reminder_at.isoformat() if self.reminder_at else None,
            "is_completed": self.is_completed,
            "attachment_url": self.attachment_url,
            "owner": self.owner,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
