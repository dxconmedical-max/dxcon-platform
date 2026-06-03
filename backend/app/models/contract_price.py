from app.extensions.db import db
from datetime import datetime
import uuid


class ContractPrice(db.Model):

    __tablename__ = "contract_prices"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    contract_id = db.Column(
        db.String(36),
        nullable=False
    )

    test_catalog_id = db.Column(
        db.String(36),
        nullable=False
    )

    standard_price = db.Column(
        db.Float,
        default=0
    )

    contract_price = db.Column(
        db.Float,
        default=0
    )

    discount_percent = db.Column(
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
            "contract_id": self.contract_id,
            "test_catalog_id": self.test_catalog_id,
            "standard_price": self.standard_price,
            "contract_price": self.contract_price,
            "discount_percent": self.discount_percent
        }
