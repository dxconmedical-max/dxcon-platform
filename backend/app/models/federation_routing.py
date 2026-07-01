from datetime import datetime
import uuid

from app.extensions.db import db


class RoutingRule(db.Model):
    __tablename__ = "federation_routing_rules"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    weight_distance = db.Column(db.Float, default=0.15)
    weight_capacity = db.Column(db.Float, default=0.15)
    weight_sla = db.Column(db.Float, default=0.15)
    weight_contract = db.Column(db.Float, default=0.1)
    weight_price = db.Column(db.Float, default=0.1)
    weight_capability = db.Column(db.Float, default=0.15)
    weight_priority = db.Column(db.Float, default=0.1)
    weight_online = db.Column(db.Float, default=0.1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "name": self.name,
            "weight_distance": self.weight_distance,
            "weight_capacity": self.weight_capacity,
            "weight_sla": self.weight_sla,
            "weight_contract": self.weight_contract,
            "weight_price": self.weight_price,
            "weight_capability": self.weight_capability,
            "weight_priority": self.weight_priority,
            "weight_online": self.weight_online,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RoutingDecision(db.Model):
    __tablename__ = "federation_routing_decisions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    decision_code = db.Column(db.String(50), unique=True, nullable=False)
    request_ref = db.Column(db.String(100))
    selected_lab_id = db.Column(db.String(36), db.ForeignKey("federated_labs.id"))
    test_code = db.Column(db.String(50))
    score_total = db.Column(db.Float, default=0)
    score_breakdown_json = db.Column(db.Text)
    candidate_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(50), default="SELECTED")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "decision_code": self.decision_code,
            "request_ref": self.request_ref,
            "selected_lab_id": self.selected_lab_id,
            "test_code": self.test_code,
            "score_total": self.score_total,
            "score_breakdown_json": self.score_breakdown_json,
            "candidate_count": self.candidate_count,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RoutingAudit(db.Model):
    __tablename__ = "federation_routing_audits"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    audit_code = db.Column(db.String(50), unique=True, nullable=False)
    routing_decision_id = db.Column(db.String(36), db.ForeignKey("federation_routing_decisions.id"))
    action = db.Column(db.String(50), nullable=False)
    actor_email = db.Column(db.String(255), default="SYSTEM")
    details_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "audit_code": self.audit_code,
            "routing_decision_id": self.routing_decision_id,
            "action": self.action,
            "actor_email": self.actor_email,
            "details_json": self.details_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
