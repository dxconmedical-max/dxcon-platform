from app.extensions.db import db
import uuid


class OrderItem(db.Model):

    __tablename__ = "order_items"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    order_id = db.Column(
        db.String(36),
        nullable=False
    )

    test_catalog_id = db.Column(
        db.String(36),
        nullable=False
    )

    price = db.Column(
        db.Float,
        default=0
    )

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "test_catalog_id": self.test_catalog_id,
            "price": self.price
        }
