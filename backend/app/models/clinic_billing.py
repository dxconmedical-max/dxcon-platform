import uuid
from datetime import datetime

from app.extensions.db import db


def _id() -> str:
    return str(uuid.uuid4())


class ClinicBillingSetting(db.Model):
    __tablename__ = "clinic_billing_settings"

    organization_id = db.Column(db.String(36), primary_key=True)
    default_discount_pct = db.Column(db.Float, nullable=False, default=0)
    payment_terms_days = db.Column(db.Integer, nullable=False, default=30)
    updated_by = db.Column(db.String(120))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClinicContract(db.Model):
    __tablename__ = "clinic_contracts"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    contract_no = db.Column(db.String(80))
    title = db.Column(db.String(200), nullable=False)
    signed_date = db.Column(db.String(10))
    start_date = db.Column(db.String(10))
    end_date = db.Column(db.String(10))
    note = db.Column(db.String(500))
    file_id = db.Column(db.String(36))
    file_name = db.Column(db.String(255))
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ClinicPrice(db.Model):
    __tablename__ = "clinic_prices"
    __table_args__ = (db.UniqueConstraint("organization_id", "test_catalog_id", name="uq_clinic_prices_org_test"),)

    id = db.Column(db.String(36), primary_key=True, default=_id)
    organization_id = db.Column(db.String(36), nullable=False)
    test_catalog_id = db.Column(db.String(36), nullable=False)
    price = db.Column(db.Float, nullable=False)
    updated_by = db.Column(db.String(120))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClinicStatement(db.Model):
    __tablename__ = "clinic_statements"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    statement_no = db.Column(db.String(40), nullable=False, unique=True)
    period_start = db.Column(db.String(10), nullable=False)
    period_end = db.Column(db.String(10), nullable=False)
    order_count = db.Column(db.Integer, nullable=False, default=0)
    total_amount = db.Column(db.Float, nullable=False, default=0)
    due_date = db.Column(db.String(10), nullable=False)
    note = db.Column(db.String(300))
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ClinicStatementLine(db.Model):
    __tablename__ = "clinic_statement_lines"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    statement_id = db.Column(db.String(36), nullable=False, index=True)
    order_code = db.Column(db.String(50), nullable=False, unique=True)
    patient_name = db.Column(db.String(255))
    amount = db.Column(db.Float, nullable=False, default=0)
    ordered_at = db.Column(db.DateTime)


class ClinicPayment(db.Model):
    __tablename__ = "clinic_payments"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    paid_at = db.Column(db.String(10), nullable=False)
    method = db.Column(db.String(40))
    reference = db.Column(db.String(120))
    note = db.Column(db.String(300))
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
