from datetime import datetime
import uuid

from app.extensions.db import db


class CollectorProof(db.Model):

    __tablename__ = "collector_proofs"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    collector_id = db.Column(db.String(36), db.ForeignKey("drivers.id"), nullable=False)

    proof_type = db.Column(db.String(50), nullable=False)

    booking_id = db.Column(db.String(36), db.ForeignKey("marketplace_bookings.id"))

    route_stop_id = db.Column(db.String(36), db.ForeignKey("collector_route_stops.id"))

    file_name = db.Column(db.String(255))

    content_base64 = db.Column(db.Text)

    signer_name = db.Column(db.String(255))

    note = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "collector_id": self.collector_id,
            "proof_type": self.proof_type,
            "booking_id": self.booking_id,
            "route_stop_id": self.route_stop_id,
            "file_name": self.file_name,
            "content_base64": self.content_base64,
            "signer_name": self.signer_name,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
