import uuid
from datetime import datetime

from app.extensions.db import db


def _id() -> str:
    return str(uuid.uuid4())


STAGES = ("LEAD", "MET", "QUOTED", "CONTRACTED", "ACTIVE", "LOST")
ACCOUNT_TYPES = ("CLINIC", "HOSPITAL", "OTHER")
ACTIVITY_KINDS = ("CALL", "VISIT", "MESSAGE", "NOTE")


class CrmAccount(db.Model):
    __tablename__ = "sales_accounts"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    name = db.Column(db.String(200), nullable=False)
    account_type = db.Column(db.String(20), nullable=False, default="CLINIC")
    organization_id = db.Column(db.String(36), unique=True)
    stage = db.Column(db.String(20), nullable=False, default="LEAD", index=True)
    owner_user_id = db.Column(db.String(36), index=True)
    owner_name = db.Column(db.String(120))
    contact_person = db.Column(db.String(120))
    phone = db.Column(db.String(40))
    address = db.Column(db.String(300))
    district = db.Column(db.String(80))
    est_monthly_cases = db.Column(db.Integer, nullable=False, default=0)
    next_followup_date = db.Column(db.String(10))
    notes = db.Column(db.String(1000))
    last_activity_at = db.Column(db.DateTime)
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CrmActivity(db.Model):
    __tablename__ = "sales_account_activities"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    account_id = db.Column(db.String(36), nullable=False, index=True)
    kind = db.Column(db.String(20), nullable=False, default="NOTE")
    summary = db.Column(db.String(1000), nullable=False)
    created_by_user_id = db.Column(db.String(36))
    created_by_name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class CrmSaleTarget(db.Model):
    __tablename__ = "sales_targets"
    __table_args__ = (db.UniqueConstraint("user_id", "month", name="uq_sales_targets_user_month"),)

    id = db.Column(db.String(36), primary_key=True, default=_id)
    user_id = db.Column(db.String(36), nullable=False)
    month = db.Column(db.String(7), nullable=False)
    target_cases = db.Column(db.Integer, nullable=False, default=0)
    target_revenue = db.Column(db.Float, nullable=False, default=0)
    updated_by = db.Column(db.String(120))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
