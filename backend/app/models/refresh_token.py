from datetime import datetime
import uuid

from app.extensions.db import db


class RefreshTokenRecord(db.Model):
    __tablename__ = "refresh_token_records"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
    )

    jti = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False,
    )

    revoked = db.Column(
        db.Boolean,
        default=False,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "jti": self.jti,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked": self.revoked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
