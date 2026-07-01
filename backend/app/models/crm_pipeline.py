from datetime import datetime
import uuid

from app.extensions.db import db


class SalesPipeline(db.Model):
    __tablename__ = "crm_sales_pipelines"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500))
    is_default = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "pipeline_code": self.pipeline_code,
            "name": self.name,
            "description": self.description,
            "is_default": self.is_default,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PipelineStage(db.Model):
    __tablename__ = "crm_pipeline_stages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pipeline_id = db.Column(
        db.String(36), db.ForeignKey("crm_sales_pipelines.id"), nullable=False
    )
    stage_code = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    sort_order = db.Column(db.Integer, default=0)
    win_probability = db.Column(db.Float, default=0)
    is_closed = db.Column(db.Boolean, default=False)
    is_won = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "pipeline_id": self.pipeline_id,
            "stage_code": self.stage_code,
            "name": self.name,
            "sort_order": self.sort_order,
            "win_probability": self.win_probability,
            "is_closed": self.is_closed,
            "is_won": self.is_won,
        }


class Opportunity(db.Model):
    __tablename__ = "crm_opportunities"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opportunity_code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    lead_id = db.Column(db.String(36), db.ForeignKey("crm_leads.id"))
    customer_id = db.Column(db.String(36), db.ForeignKey("crm_customers.id"))
    organization_id = db.Column(db.String(36), db.ForeignKey("crm_organizations.id"))
    pipeline_id = db.Column(db.String(36), db.ForeignKey("crm_sales_pipelines.id"))
    pipeline_stage = db.Column(db.String(50), default="LEAD")
    amount = db.Column(db.Float, default=0)
    currency = db.Column(db.String(10), default="VND")
    expected_close_date = db.Column(db.Date)
    status = db.Column(db.String(50), default="OPEN")
    owner = db.Column(db.String(255))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "opportunity_code": self.opportunity_code,
            "title": self.title,
            "lead_id": self.lead_id,
            "customer_id": self.customer_id,
            "organization_id": self.organization_id,
            "pipeline_id": self.pipeline_id,
            "pipeline_stage": self.pipeline_stage,
            "amount": self.amount,
            "currency": self.currency,
            "expected_close_date": (
                self.expected_close_date.isoformat() if self.expected_close_date else None
            ),
            "status": self.status,
            "owner": self.owner,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
