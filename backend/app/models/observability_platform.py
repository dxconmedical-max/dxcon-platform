from datetime import datetime
import uuid

from app.extensions.db import db


class AuditTimeline(db.Model):
    __tablename__ = "obs_audit_timelines"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timeline_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "timeline_code": self.timeline_code,
            "name": self.name,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditActor(db.Model):
    __tablename__ = "obs_audit_actors"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_code = db.Column(db.String(50), unique=True, nullable=False)
    actor_type = db.Column(db.String(50), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "actor_code": self.actor_code,
            "actor_type": self.actor_type,
            "display_name": self.display_name,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditResource(db.Model):
    __tablename__ = "obs_audit_resources"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource_code = db.Column(db.String(50), unique=True, nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "resource_code": self.resource_code,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditEvent(db.Model):
    __tablename__ = "obs_audit_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_code = db.Column(db.String(50), unique=True, nullable=False)
    timeline_id = db.Column(db.String(36), db.ForeignKey("obs_audit_timelines.id"))
    actor_id = db.Column(db.String(36), db.ForeignKey("obs_audit_actors.id"))
    resource_id = db.Column(db.String(36), db.ForeignKey("obs_audit_resources.id"))
    event_type = db.Column(db.String(100), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    module = db.Column(db.String(100))
    request_id = db.Column(db.String(100))
    trace_id = db.Column(db.String(100))
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_code": self.event_code,
            "timeline_id": self.timeline_id,
            "actor_id": self.actor_id,
            "resource_id": self.resource_id,
            "event_type": self.event_type,
            "action": self.action,
            "module": self.module,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ObsHealthEvent(db.Model):
    __tablename__ = "obs_health_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    component = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    detail_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "component": self.component,
            "status": self.status,
            "detail_json": self.detail_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ObsMetricSnapshot(db.Model):
    __tablename__ = "obs_metric_snapshots"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_name = db.Column(db.String(100), nullable=False)
    metric_type = db.Column(db.String(50), default="counter")
    value = db.Column(db.Float, default=0)
    labels_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "metric_name": self.metric_name,
            "metric_type": self.metric_type,
            "value": self.value,
            "labels_json": self.labels_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ObsAlert(db.Model):
    __tablename__ = "obs_alerts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_code = db.Column(db.String(50), unique=True, nullable=False)
    rule_code = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.String(50), default="MEDIUM")
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default="OPEN")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "alert_code": self.alert_code,
            "rule_code": self.rule_code,
            "severity": self.severity,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
