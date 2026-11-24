from datetime import datetime
import uuid

from app.extensions.db import db


class TestFlag(db.Model):
    """Extra per-test settings (send-out / add-on window), kept apart from the core test catalog."""

    __test__ = False  # not a pytest class
    __tablename__ = "test_flags"

    test_catalog_id = db.Column(db.String(36), primary_key=True)
    is_sendout = db.Column(db.Boolean, nullable=False, default=False)
    sendout_destination = db.Column(db.String(120))
    sendout_eta_days = db.Column(db.Integer)
    addon_window_hours = db.Column(db.Integer)
    updated_by = db.Column(db.String(120))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OrderAddon(db.Model):
    __tablename__ = "order_addons"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    original_order_code = db.Column(db.String(50), nullable=False, index=True)
    addon_order_code = db.Column(db.String(50), nullable=False, unique=True)
    tests_json = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SendoutTrack(db.Model):
    __tablename__ = "sendout_tracks"
    __table_args__ = (db.UniqueConstraint("order_code", "test_code", name="uq_sendout_tracks_order_test"),)

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_code = db.Column(db.String(50), nullable=False)
    test_code = db.Column(db.String(50), nullable=False)
    sent_at = db.Column(db.String(10))
    destination = db.Column(db.String(120))
    eta_date = db.Column(db.String(10))
    note = db.Column(db.String(300))
    dismissed = db.Column(db.Boolean, nullable=False, default=False)
    updated_by = db.Column(db.String(120))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
