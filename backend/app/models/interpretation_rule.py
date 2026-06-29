from datetime import datetime
import uuid

from app.extensions.db import db


class InterpretationRule(db.Model):

    __tablename__ = "interpretation_rules"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    rule_code = db.Column(db.String(50), unique=True, nullable=False)

    test_code = db.Column(db.String(50))

    test_name_pattern = db.Column(db.String(255))

    condition_flag = db.Column(db.String(20), default="ANY")

    risk_level = db.Column(db.String(20), default="LOW")

    finding_en = db.Column(db.Text)

    finding_vi = db.Column(db.Text)

    recommendation_en = db.Column(db.Text)

    recommendation_vi = db.Column(db.Text)

    priority = db.Column(db.Integer, default=100)

    status = db.Column(db.String(20), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "test_code": self.test_code,
            "test_name_pattern": self.test_name_pattern,
            "condition_flag": self.condition_flag,
            "risk_level": self.risk_level,
            "finding_en": self.finding_en,
            "finding_vi": self.finding_vi,
            "recommendation_en": self.recommendation_en,
            "recommendation_vi": self.recommendation_vi,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
