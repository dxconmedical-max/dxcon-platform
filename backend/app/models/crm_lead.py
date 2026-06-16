from app.extensions.db import db
from datetime import datetime
import uuid


class CrmLead(db.Model):

    __tablename__ = "crm_leads"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    lead_code = db.Column(db.String(50), unique=True, nullable=False)

    company_name = db.Column(db.String(255))

    contact_person = db.Column(db.String(255))

    phone = db.Column(db.String(50))

    email = db.Column(db.String(255))

    lead_source = db.Column(db.String(100))

    pipeline_stage = db.Column(
        db.String(50),
        default="LEAD"
    )

    estimated_revenue = db.Column(
        db.Float,
        default=0
    )

    owner = db.Column(db.String(255))

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
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
            "pipeline_stage": self.pipeline_stage,
            "estimated_revenue": self.estimated_revenue,
            "owner": self.owner
        }
