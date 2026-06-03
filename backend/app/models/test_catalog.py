from app.extensions.db import db
from datetime import datetime
import uuid


class TestCatalog(db.Model):

    __tablename__ = "test_catalogs"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    code = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    name = db.Column(
        db.String(255),
        nullable=False
    )

    category = db.Column(
        db.String(100)
    )

    sample_type = db.Column(
        db.String(100)
    )

    price = db.Column(
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
            "code": self.code,
            "name": self.name,
            "category": self.category,
            "sample_type": self.sample_type,
            "price": self.price
        }
