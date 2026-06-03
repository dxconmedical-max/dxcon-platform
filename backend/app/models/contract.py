from app.extensions.db import db
from datetime import datetime
import uuid


class Contract(db.Model):

    __tablename__ = "contracts"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    contract_code = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    company_id = db.Column(
        db.String(36),
        nullable=False
    )

    title = db.Column(
        db.String(255),
        nullable=False
    )

    contract_type = db.Column(
        db.String(100),
        default="SERVICE"
    )

    start_date = db.Column(
        db.String(20)
    )

    end_date = db.Column(
        db.String(20)
    )

    status = db.Column(
        db.String(50),
        default="DRAFT"
    )

    total_value = db.Column(
        db.Float,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def to_dict(self):
        return {
            "id": self.id,
            "contract_code": self.contract_code,
            "company_id": self.company_id,
            "title": self.title,
            "contract_type": self.contract_type,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "total_value": self.total_value
        }
