from datetime import datetime
import uuid

from app.extensions.db import db


class FederatedLab(db.Model):
    __tablename__ = "federated_labs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lab_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    provider_id = db.Column(db.String(36), db.ForeignKey("federation_providers.id"))
    partner_id = db.Column(db.String(36))
    city = db.Column(db.String(100))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    status = db.Column(db.String(50), default="OFFLINE")
    connection_status = db.Column(db.String(50), default="DISCONNECTED")
    priority = db.Column(db.Integer, default=50)
    sla_minutes = db.Column(db.Integer, default=240)
    contract_active = db.Column(db.Boolean, default=True)
    base_price = db.Column(db.Float, default=0)
    metadata_json = db.Column(db.Text, default="{}")
    connected_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "lab_code": self.lab_code,
            "name": self.name,
            "provider_id": self.provider_id,
            "partner_id": self.partner_id,
            "city": self.city,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "status": self.status,
            "connection_status": self.connection_status,
            "priority": self.priority,
            "sla_minutes": self.sla_minutes,
            "contract_active": self.contract_active,
            "base_price": self.base_price,
            "metadata_json": self.metadata_json,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class FederationProvider(db.Model):
    __tablename__ = "federation_providers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    provider_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    provider_type = db.Column(db.String(50), default="LAB_NETWORK")
    contact_email = db.Column(db.String(255))
    contact_phone = db.Column(db.String(30))
    status = db.Column(db.String(50), default="ACTIVE")
    settings_json = db.Column(db.Text, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "provider_code": self.provider_code,
            "name": self.name,
            "provider_type": self.provider_type,
            "contact_email": self.contact_email,
            "contact_phone": self.contact_phone,
            "status": self.status,
            "settings_json": self.settings_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FederationProviderBranch(db.Model):
    __tablename__ = "federation_provider_branches"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    branch_code = db.Column(db.String(50), unique=True, nullable=False)
    provider_id = db.Column(db.String(36), db.ForeignKey("federation_providers.id"), nullable=False)
    federated_lab_id = db.Column(db.String(36), db.ForeignKey("federated_labs.id"))
    name = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100))
    address = db.Column(db.Text)
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "branch_code": self.branch_code,
            "provider_id": self.provider_id,
            "federated_lab_id": self.federated_lab_id,
            "name": self.name,
            "city": self.city,
            "address": self.address,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FederationCapability(db.Model):
    __tablename__ = "federation_capabilities"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    capability_code = db.Column(db.String(50), nullable=False)
    federated_lab_id = db.Column(db.String(36), db.ForeignKey("federated_labs.id"), nullable=False)
    test_code = db.Column(db.String(50))
    test_name = db.Column(db.String(255), nullable=False)
    modality = db.Column(db.String(50), default="LAB")
    is_active = db.Column(db.Boolean, default=True)
    turnaround_hours = db.Column(db.Integer, default=24)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "capability_code": self.capability_code,
            "federated_lab_id": self.federated_lab_id,
            "test_code": self.test_code,
            "test_name": self.test_name,
            "modality": self.modality,
            "is_active": self.is_active,
            "turnaround_hours": self.turnaround_hours,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FederationPolicy(db.Model):
    __tablename__ = "federation_policies"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    policy_type = db.Column(db.String(50), default="ROUTING")
    provider_id = db.Column(db.String(36), db.ForeignKey("federation_providers.id"))
    rules_json = db.Column(db.Text, default="{}")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "policy_code": self.policy_code,
            "name": self.name,
            "policy_type": self.policy_type,
            "provider_id": self.provider_id,
            "rules_json": self.rules_json,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FederationEvent(db.Model):
    __tablename__ = "federation_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_code = db.Column(db.String(50), unique=True, nullable=False)
    federated_lab_id = db.Column(db.String(36), db.ForeignKey("federated_labs.id"))
    provider_id = db.Column(db.String(36), db.ForeignKey("federation_providers.id"))
    event_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text)
    severity = db.Column(db.String(20), default="INFO")
    metadata_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "event_code": self.event_code,
            "federated_lab_id": self.federated_lab_id,
            "provider_id": self.provider_id,
            "event_type": self.event_type,
            "message": self.message,
            "severity": self.severity,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
