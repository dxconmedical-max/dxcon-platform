from datetime import datetime
import uuid

from app.extensions.db import db


class FailoverRule(db.Model):
    __tablename__ = "federation_failover_rules"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    trigger_type = db.Column(db.String(50), nullable=False)
    target_lab_id = db.Column(db.String(36), db.ForeignKey("federated_labs.id"))
    fallback_lab_id = db.Column(db.String(36), db.ForeignKey("federated_labs.id"))
    is_active = db.Column(db.Boolean, default=True)
    config_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "name": self.name,
            "trigger_type": self.trigger_type,
            "target_lab_id": self.target_lab_id,
            "fallback_lab_id": self.fallback_lab_id,
            "is_active": self.is_active,
            "config_json": self.config_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FailoverEvent(db.Model):
    __tablename__ = "federation_failover_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_code = db.Column(db.String(50), unique=True, nullable=False)
    trigger_type = db.Column(db.String(50), nullable=False)
    source_lab_id = db.Column(db.String(36), db.ForeignKey("federated_labs.id"))
    fallback_lab_id = db.Column(db.String(36), db.ForeignKey("federated_labs.id"))
    status = db.Column(db.String(50), default="TRIGGERED")
    message = db.Column(db.Text)
    metadata_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_code": self.event_code,
            "trigger_type": self.trigger_type,
            "source_lab_id": self.source_lab_id,
            "fallback_lab_id": self.fallback_lab_id,
            "status": self.status,
            "message": self.message,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
