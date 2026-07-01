from datetime import datetime
import uuid

from app.extensions.db import db


class ApiClient(db.Model):
    __tablename__ = "api_clients"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    organization = db.Column(db.String(255))
    contact_email = db.Column(db.String(255))
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "client_code": self.client_code,
            "name": self.name,
            "organization": self.organization,
            "contact_email": self.contact_email,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ApiKey(db.Model):
    __tablename__ = "api_keys"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey("api_clients.id"), nullable=False)
    key_prefix = db.Column(db.String(20), nullable=False, index=True)
    key_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="ACTIVE")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked_at = db.Column(db.DateTime)

    def to_dict(self, include_client=False):
        payload = {
            "id": self.id,
            "client_id": self.client_id,
            "key_prefix": self.key_prefix,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
        }
        if include_client:
            payload["client"] = self.client_id
        return payload


class ApiUsageLog(db.Model):
    __tablename__ = "api_usage_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey("api_clients.id"))
    api_key_id = db.Column(db.String(36), db.ForeignKey("api_keys.id"))
    method = db.Column(db.String(20), nullable=False)
    path = db.Column(db.String(500), nullable=False)
    status_code = db.Column(db.Integer)
    duration_ms = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "api_key_id": self.api_key_id,
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
