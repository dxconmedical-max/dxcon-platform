import uuid
from datetime import datetime

from app.extensions.db import db


def _id() -> str:
    return str(uuid.uuid4())


class LabPartner(db.Model):
    __tablename__ = "lab_partners"

    organization_id = db.Column(db.String(36), primary_key=True)
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LabCostPrice(db.Model):
    __tablename__ = "lab_cost_prices"
    __table_args__ = (db.UniqueConstraint("organization_id", "test_catalog_id", name="uq_lab_cost_prices_org_test"),)

    id = db.Column(db.String(36), primary_key=True, default=_id)
    organization_id = db.Column(db.String(36), nullable=False)
    test_catalog_id = db.Column(db.String(36), nullable=False)
    cost = db.Column(db.Float, nullable=False)
    updated_by = db.Column(db.String(120))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LabRouting(db.Model):
    __tablename__ = "lab_routing"

    scope_org_id = db.Column(db.String(36), primary_key=True)
    lab_organization_id = db.Column(db.String(36), nullable=False)
    updated_by = db.Column(db.String(120))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OrderLabCost(db.Model):
    __tablename__ = "order_lab_costs"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    order_code = db.Column(db.String(50), nullable=False, unique=True)
    lab_organization_id = db.Column(db.String(36), nullable=False, index=True)
    cost_total = db.Column(db.Float, nullable=False, default=0)
    sell_total = db.Column(db.Float, nullable=False, default=0)
    missing_count = db.Column(db.Integer, nullable=False, default=0)
    assigned_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LabPayableStatement(db.Model):
    __tablename__ = "lab_payable_statements"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    statement_no = db.Column(db.String(40), nullable=False, unique=True)
    period_start = db.Column(db.String(10), nullable=False)
    period_end = db.Column(db.String(10), nullable=False)
    order_count = db.Column(db.Integer, nullable=False, default=0)
    total_amount = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="open")
    note = db.Column(db.String(300))
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LabPayableLine(db.Model):
    __tablename__ = "lab_payable_lines"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    statement_id = db.Column(db.String(36), nullable=False, index=True)
    order_code = db.Column(db.String(50), nullable=False, unique=True)
    amount = db.Column(db.Float, nullable=False, default=0)


class LabPayment(db.Model):
    __tablename__ = "lab_payments"

    id = db.Column(db.String(36), primary_key=True, default=_id)
    organization_id = db.Column(db.String(36), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    paid_at = db.Column(db.String(10), nullable=False)
    method = db.Column(db.String(40))
    reference = db.Column(db.String(120))
    note = db.Column(db.String(300))
    created_by = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
