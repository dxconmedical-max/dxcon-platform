"""Additive pilot business-engine tables (Sprint 1)."""

from __future__ import annotations

from datetime import datetime
import uuid

from app.extensions.db import db


class BizOrder(db.Model):
    __tablename__ = "biz_orders"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_code = db.Column(db.String(50), unique=True, nullable=False)
    patient_code = db.Column(db.String(50), db.ForeignKey("patients.patient_code"), nullable=False)
    patient_name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default="draft", nullable=False)
    subtotal = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    barcode_value = db.Column(db.String(100), unique=True)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship("BizOrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_items: bool = True) -> dict:
        payload = {
            "id": self.id,
            "order_code": self.order_code,
            "patient_code": self.patient_code,
            "patient_id": self.patient_code,
            "patient_name": self.patient_name,
            "status": self.status,
            "subtotal": self.subtotal,
            "discount": self.discount,
            "total_amount": self.total_amount,
            "barcode_value": self.barcode_value,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_items:
            payload["items"] = [item.to_dict() for item in self.items]
        return payload


class BizOrderItem(db.Model):
    __tablename__ = "biz_order_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(db.String(36), db.ForeignKey("biz_orders.id"), nullable=False)
    test_catalog_id = db.Column(db.String(36))
    test_code = db.Column(db.String(50), nullable=False)
    test_name = db.Column(db.String(255), nullable=False)
    unit_price = db.Column(db.Float, default=0)
    quantity = db.Column(db.Integer, default=1)
    line_total = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "test_catalog_id": self.test_catalog_id,
            "test_code": self.test_code,
            "test_name": self.test_name,
            "unit_price": self.unit_price,
            "quantity": self.quantity,
            "line_total": self.line_total,
        }


class BizInvoice(db.Model):
    __tablename__ = "biz_invoices"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_no = db.Column(db.String(50), unique=True, nullable=False)
    order_id = db.Column(db.String(36), db.ForeignKey("biz_orders.id"), nullable=False)
    amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default="unpaid", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "invoice_no": self.invoice_no,
            "order_id": self.order_id,
            "amount": self.amount,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BizPayment(db.Model):
    __tablename__ = "biz_payments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = db.Column(db.String(36), db.ForeignKey("biz_invoices.id"), nullable=False)
    order_id = db.Column(db.String(36), db.ForeignKey("biz_orders.id"), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    receipt_number = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, default=0)
    paid_at = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "order_id": self.order_id,
            "payment_method": self.payment_method,
            "receipt_number": self.receipt_number,
            "amount": self.amount,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_by": self.created_by,
        }


class BizCollection(db.Model):
    __tablename__ = "biz_collections"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(db.String(36), db.ForeignKey("biz_orders.id"), nullable=False)
    collector_name = db.Column(db.String(255))
    pickup_address = db.Column(db.Text)
    scheduled_at = db.Column(db.DateTime)
    status = db.Column(db.String(50), default="assigned", nullable=False)
    sample_code = db.Column(db.String(50), unique=True)
    barcode_value = db.Column(db.String(100), unique=True)
    accession_number = db.Column(db.String(50), unique=True)
    received_by = db.Column(db.String(255))
    received_at = db.Column(db.DateTime)
    condition_status = db.Column(db.String(30))
    receive_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "order_id": self.order_id,
            "collector_name": self.collector_name,
            "pickup_address": self.pickup_address,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "status": self.status,
            "sample_code": self.sample_code,
            "barcode_value": self.barcode_value,
            "accession_number": self.accession_number,
            "received_by": self.received_by,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "condition_status": self.condition_status,
            "receive_note": self.receive_note,
        }


class BizResult(db.Model):
    __tablename__ = "biz_results"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    result_code = db.Column(db.String(50), unique=True, nullable=False)
    order_id = db.Column(db.String(36), db.ForeignKey("biz_orders.id"), nullable=False, unique=True)
    status = db.Column(db.String(50), default="testing", nullable=False)
    doctor_note = db.Column(db.Text)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.String(255))
    released_at = db.Column(db.DateTime)
    html_content = db.Column(db.Text)
    patient_visible = db.Column(db.Boolean, default=False)
    workflow_status = db.Column(db.String(30), default="draft")
    result_source = db.Column(db.String(30), default="manual")
    import_batch_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship("BizResultItem", backref="result", lazy=True, cascade="all, delete-orphan")

    def to_dict(self, include_items: bool = True) -> dict:
        payload = {
            "id": self.id,
            "result_code": self.result_code,
            "order_id": self.order_id,
            "status": self.status,
            "doctor_note": self.doctor_note,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "patient_visible": self.patient_visible,
            "workflow_status": self.workflow_status,
            "result_source": self.result_source,
            "import_batch_id": self.import_batch_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_items:
            payload["items"] = [item.to_dict() for item in self.items]
        return payload


class BizResultItem(db.Model):
    __tablename__ = "biz_result_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    result_id = db.Column(db.String(36), db.ForeignKey("biz_results.id"), nullable=False)
    test_code = db.Column(db.String(50))
    test_name = db.Column(db.String(255), nullable=False)
    result_value = db.Column(db.String(255))
    unit = db.Column(db.String(50))
    reference_range = db.Column(db.String(255))
    flag = db.Column(db.String(20), default="NORMAL")
    instrument = db.Column(db.String(100))
    technician = db.Column(db.String(255))
    result_time = db.Column(db.DateTime)
    entry_note = db.Column(db.Text)
    specimen_id = db.Column(db.String(36))
    order_item_id = db.Column(db.String(36))
    original_value = db.Column(db.Text)
    normalized_value = db.Column(db.Text)
    critical_flag = db.Column(db.Boolean, default=False)
    analyzer_flags_json = db.Column(db.Text)
    result_status = db.Column(db.String(30), default="PENDING")
    technician_reviewer = db.Column(db.String(255))
    doctor_approver = db.Column(db.String(255))
    reviewed_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    version = db.Column(db.Integer, default=1)
    amendment_of = db.Column(db.String(36))
    audit_reference = db.Column(db.String(36))
    preliminary_result_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "result_id": self.result_id,
            "test_code": self.test_code,
            "test_name": self.test_name,
            "result_value": self.result_value,
            "unit": self.unit,
            "reference_range": self.reference_range,
            "flag": self.flag,
            "result_status": self.result_status,
            "original_value": self.original_value,
            "normalized_value": self.normalized_value,
            "critical_flag": self.critical_flag,
            "version": self.version,
        }


class BizWorkflowAudit(db.Model):
    __tablename__ = "biz_workflow_audits"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor = db.Column(db.String(255), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.String(100), nullable=False)
    old_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50))
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "actor": self.actor,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "note": self.note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
