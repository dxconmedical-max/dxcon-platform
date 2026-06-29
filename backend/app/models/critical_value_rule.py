from datetime import datetime
import uuid

from app.extensions.db import db


class CriticalValueRule(db.Model):

    __tablename__ = "critical_value_rules"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    rule_code = db.Column(db.String(50), unique=True, nullable=False)

    test_code = db.Column(db.String(50), nullable=False)

    test_name = db.Column(db.String(255))

    panic_low = db.Column(db.Float)

    panic_high = db.Column(db.Float)

    severity = db.Column(db.String(20), default="CRITICAL")

    message_en = db.Column(db.Text)

    message_vi = db.Column(db.Text)

    status = db.Column(db.String(20), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "test_code": self.test_code,
            "test_name": self.test_name,
            "panic_low": self.panic_low,
            "panic_high": self.panic_high,
            "severity": self.severity,
            "message_en": self.message_en,
            "message_vi": self.message_vi,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
