from datetime import datetime
import uuid

from app.extensions.db import db


class CrmLead(db.Model):

    __tablename__ = "crm_leads"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    lead_code = db.Column(db.String(50), unique=True, nullable=False)

    company_name = db.Column(db.String(255))

    contact_person = db.Column(db.String(255))

    phone = db.Column(db.String(50))

    email = db.Column(db.String(255))

    lead_source = db.Column(db.String(100))

    organization_id = db.Column(db.String(36), db.ForeignKey("crm_organizations.id"))

    pipeline_stage = db.Column(
        db.String(50),
        default="LEAD",
    )

    status = db.Column(db.String(50), default="NEW")

    estimated_revenue = db.Column(
        db.Float,
        default=0,
    )

    owner = db.Column(db.String(255))

    notes = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "lead_code": self.lead_code,
            "company_name": self.company_name,
            "contact_person": self.contact_person,
            "phone": self.phone,
            "email": self.email,
            "lead_source": self.lead_source,
            "organization_id": self.organization_id,
            "pipeline_stage": self.pipeline_stage,
            "status": self.status,
            "estimated_revenue": self.estimated_revenue,
            "owner": self.owner,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


Lead = CrmLead
