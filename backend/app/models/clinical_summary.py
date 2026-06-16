from app.extensions.db import db
from datetime import datetime
import uuid


class ClinicalSummary(db.Model):

    __tablename__ = "clinical_summaries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(db.String(36), nullable=False)
    risk_level = db.Column(db.String(50), default="LOW")
    findings = db.Column(db.Text)
    recommendations = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "risk_level": self.risk_level,
            "findings": self.findings,
            "recommendations": self.recommendations,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
