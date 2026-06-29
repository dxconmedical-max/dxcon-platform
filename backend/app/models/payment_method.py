from datetime import datetime
import uuid

from app.extensions.db import db


class PaymentMethod(db.Model):

    __tablename__ = "payment_methods"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    owner_type = db.Column(db.String(50), nullable=False)

    owner_id = db.Column(db.String(36), nullable=False)

    method_type = db.Column(db.String(50), nullable=False)

    provider = db.Column(db.String(50), nullable=False)

    display_name = db.Column(db.String(255))

    token_ref = db.Column(db.String(255))

    last4 = db.Column(db.String(4))

    is_default = db.Column(db.Boolean, default=False)

    status = db.Column(db.String(20), default="ACTIVE")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "owner_type": self.owner_type,
            "owner_id": self.owner_id,
            "method_type": self.method_type,
            "provider": self.provider,
            "display_name": self.display_name,
            "token_ref": self.token_ref,
            "last4": self.last4,
            "is_default": self.is_default,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
