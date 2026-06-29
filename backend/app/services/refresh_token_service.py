from datetime import datetime

from app.extensions.db import db
from app.models.refresh_token import RefreshTokenRecord


class RefreshTokenService:
    @staticmethod
    def register(user_id, jti, expires_at):
        record = RefreshTokenRecord(
            user_id=user_id,
            jti=jti,
            expires_at=expires_at,
            revoked=False,
        )
        db.session.add(record)
        return record

    @staticmethod
    def is_revoked(jti):
        if not jti:
            return True

        record = RefreshTokenRecord.query.filter_by(jti=jti).first()
        if not record:
            return False

        if record.revoked:
            return True

        if record.expires_at and record.expires_at < datetime.utcnow():
            return True

        return False

    @staticmethod
    def revoke(jti):
        record = RefreshTokenRecord.query.filter_by(jti=jti).first()
        if not record:
            return None

        record.revoked = True
        return record
