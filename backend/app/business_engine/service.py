"""Production business engine — patient through report release."""

from __future__ import annotations

from datetime import datetime, timezone
import re
import uuid

from sqlalchemy import or_

from app.business_engine.audit import write_biz_audit
from app.business_engine.statuses import (
    COLLECTION_ASSIGNED,
    COLLECTION_ACCEPTED,
    COLLECTION_COLLECTED,
    COLLECTION_DELIVERED,
    COLLECTION_IN_TRANSIT,
    INVOICE_PAID,
    INVOICE_UNPAID,
    ORDER_APPROVED,
    ORDER_COLLECTED,
    ORDER_DRAFT,
    ORDER_IN_TRANSIT,
    ORDER_LAB_RECEIVED,
    ORDER_PAID,
    ORDER_PAYMENT_PENDING,
    ORDER_PENDING_REVIEW,
    ORDER_RELEASED,
    ORDER_SAMPLING,
    ORDER_TESTING,
    ORDER_TRANSITIONS,
    RESULT_APPROVED,
    RESULT_PENDING_REVIEW,
    RESULT_RELEASED,
    RESULT_TESTING,
)
from app.core.db_introspection import table_has_column as _table_has_column
from app.extensions.db import db
from app.models.biz_order import (
    BizCollection,
    BizInvoice,
    BizOrder,
    BizOrderItem,
    BizPayment,
    BizResult,
    BizResultItem,
    BizWorkflowAudit,
)
from app.models.patient import Patient
from app.models.patient_profile import PatientProfile
from app.models.test_catalog import TestCatalog


class BusinessEngineError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def table_has_column(table_name: str, column_name: str) -> bool:
    """Local wrapper around the shared DB introspection helper."""
    return _table_has_column(db, table_name, column_name)


def _code(prefix: str) -> str:
    return f"{prefix}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


def _normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    return re.sub(r"\s+", "", phone.strip())


def _transition_order(order: BizOrder, new_status: str, *, action: str, note: str | None = None, actor: str | None = None) -> BizOrder:
    allowed = ORDER_TRANSITIONS.get(order.status, [])
    if new_status not in allowed:
        raise BusinessEngineError(f"Cannot transition order from {order.status} to {new_status}")
    old = order.status
    order.status = new_status
    order.updated_at = _utcnow()
    write_biz_audit(
        action=action,
        entity_type="order",
        entity_id=order.order_code,
        old_status=old,
        new_status=new_status,
        note=note,
        actor=actor,
    )
    return order


def _get_order(order_ref: str) -> BizOrder:
    order = BizOrder.query.filter(
        or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)
    ).first()
    if not order:
        raise BusinessEngineError(f"Order not found: {order_ref}")
    return order


def _recalc_order_totals(order: BizOrder) -> None:
    subtotal = sum(item.line_total for item in order.items)
    order.subtotal = round(subtotal, 2)
    order.total_amount = round(max(subtotal - (order.discount or 0), 0), 2)


def _qr_payload(patient_code: str) -> str:
    return f"dxcon:patient:{patient_code}"


# --- Patient ---


def create_patient(
    *,
    full_name: str,
    phone: str | None = None,
    email: str | None = None,
    gender: str | None = None,
    date_of_birth: str | None = None,
    address: str | None = None,
    national_id: str | None = None,
    patient_code: str | None = None,
    actor: str | None = None,
) -> Patient:
    if not full_name or not full_name.strip():
        raise BusinessEngineError("full_name is required")
    phone_norm = _normalize_phone(phone)
    if phone_norm:
        existing = Patient.query.filter_by(phone=phone_norm).first()
        if existing:
            raise BusinessEngineError(f"Patient with phone {phone_norm} already exists")
    if national_id and national_id.strip():
        existing_nid = Patient.query.filter_by(national_id=national_id.strip()).first()
        if existing_nid:
            raise BusinessEngineError(f"Patient with national_id already exists")
    code = (patient_code or _code("P")).strip()
    if Patient.query.get(code):
        raise BusinessEngineError(f"Patient code already exists: {code}")
    phone_norm = _normalize_phone(phone)
    if table_has_column("patients", "id"):
        created_at = _utcnow()
        db.session.execute(
            db.text(
                "INSERT INTO patients (id, patient_code, full_name, gender, date_of_birth, phone, email, address, national_id, created_at) "
                "VALUES (:id, :patient_code, :full_name, :gender, :date_of_birth, :phone, :email, :address, :national_id, :created_at)"
            ),
            {
                "id": code,
                "patient_code": code,
                "full_name": full_name.strip(),
                "gender": (gender or "").strip() or None,
                "date_of_birth": (date_of_birth or "").strip() or None,
                "phone": phone_norm,
                "email": (email or "").strip() or None,
                "address": (address or "").strip() or None,
                "national_id": (national_id or "").strip() or None,
                "created_at": created_at,
            },
        )
        patient = Patient.query.get(code)
    else:
        patient = Patient(
            patient_code=code,
            full_name=full_name.strip(),
            phone=phone_norm,
            email=(email or "").strip() or None,
            gender=(gender or "").strip() or None,
            date_of_birth=(date_of_birth or "").strip() or None,
            address=(address or "").strip() or None,
            national_id=(national_id or "").strip() or None,
        )
        db.session.add(patient)
    profile = PatientProfile(
        patient_id=code,
        qr_code=code,
        qr_payload=_qr_payload(code),
    )
    db.session.add(profile)
    write_biz_audit(action="patient.create", entity_type="patient", entity_id=code, new_status="active", actor=actor)
    db.session.flush()
    return patient


def update_patient(patient_code: str, **fields) -> Patient:
    patient = Patient.query.get(patient_code)
    if not patient:
        raise BusinessEngineError("Patient not found")
    phone = fields.get("phone")
    if phone is not None:
        phone_norm = _normalize_phone(phone)
        if phone_norm:
            clash = Patient.query.filter(Patient.phone == phone_norm, Patient.patient_code != patient_code).first()
            if clash:
                raise BusinessEngineError("Phone already used by another patient")
        patient.phone = phone_norm
    national_id = fields.get("national_id")
    if national_id is not None and national_id.strip():
        clash = Patient.query.filter(
            Patient.national_id == national_id.strip(),
            Patient.patient_code != patient_code,
        ).first()
        if clash:
            raise BusinessEngineError("national_id already used")
        patient.national_id = national_id.strip()
    for key in ("full_name", "email", "gender", "date_of_birth", "address"):
        if key in fields and fields[key] is not None:
            setattr(patient, key, str(fields[key]).strip() or None)
    write_biz_audit(action="patient.update", entity_type="patient", entity_id=patient_code, note="profile updated")
    return patient


def get_patient(patient_code: str) -> Patient | None:
    return Patient.query.get(patient_code)


def search_patients(query: str, limit: int = 20) -> list[Patient]:
    q = (query or "").strip()
    if not q:
        return Patient.query.order_by(Patient.created_at.desc()).limit(limit).all()
    pattern = f"%{q}%"
    lowered = q.lower()
    return (
        Patient.query.filter(
            or_(
                Patient.patient_code.like(pattern),
                Patient.full_name.like(pattern),
                Patient.phone.like(pattern),
                Patient.national_id.like(pattern),
                db.func.lower(Patient.full_name).like(f"%{lowered}%"),
            )
        )
        .order_by(Patient.created_at.desc())
        .limit(limit)
        .all()
    )


def patient_to_detail(patient: Patient) -> dict:
    profile = PatientProfile.query.filter_by(patient_id=patient.patient_code).first()
    orders = BizOrder.query.filter_by(patient_code=patient.patient_code).order_by(BizOrder.created_at.desc()).all()
    invoices = []
    reports = []
    for order in orders:
        inv = BizInvoice.query.filter_by(order_id=order.id).first()
        if inv:
            invoices.append(inv)
        res = BizResult.query.filter_by(order_id=order.id).first()
        if res:
            reports.append(res)
    return {
        **patient.to_dict(),
        "qr_payload": profile.qr_payload if profile else _qr_payload(patient.patient_code),
        "orders": [o.to_dict(include_items=False) for o in orders],
        "invoices": [i.to_dict() for i in invoices],
        "reports": [r.to_dict() for r in reports],
    }


# --- Order ---


def create_order(
    *,
    patient_code: str,
    test_catalog_ids: list[str] | None = None,
    discount: float = 0,
    note: str | None = None,
    actor: str | None = None,
) -> BizOrder:
    patient = Patient.query.get(patient_code)
    if not patient:
        raise BusinessEngineError("Patient not found")
    order = BizOrder(
        order_code=_code("ORD"),
        patient_code=patient.patient_code,
        patient_name=patient.full_name,
        status=ORDER_DRAFT,
        discount=float(discount or 0),
        note=note,
    )
    db.session.add(order)
    db.session.flush()
    catalog_ids = test_catalog_ids or []
    if not catalog_ids:
        default_tests = TestCatalog.query.limit(1).all()
        catalog_ids = [t.id for t in default_tests]
    if not catalog_ids:
        raise BusinessEngineError("No test catalog items available")
    for catalog_id in catalog_ids:
        add_order_item(order.id, catalog_id)
    _recalc_order_totals(order)
    write_biz_audit(
        action="order.create",
        entity_type="order",
        entity_id=order.order_code,
        new_status=ORDER_DRAFT,
        actor=actor,
    )
    return order


def add_order_item(order_id: str, test_catalog_id: str, quantity: int = 1) -> BizOrderItem:
    order = BizOrder.query.get(order_id)
    if not order:
        raise BusinessEngineError("Order not found")
    if order.status != ORDER_DRAFT:
        raise BusinessEngineError("Items can only be added to draft orders")
    catalog = TestCatalog.query.get(test_catalog_id)
    if not catalog:
        raise BusinessEngineError("Test catalog item not found")
    qty = max(int(quantity or 1), 1)
    line_total = round((catalog.price or 0) * qty, 2)
    item = BizOrderItem(
        order_id=order.id,
        test_catalog_id=catalog.id,
        test_code=catalog.code,
        test_name=catalog.name,
        unit_price=catalog.price or 0,
        quantity=qty,
        line_total=line_total,
    )
    db.session.add(item)
    db.session.flush()
    _recalc_order_totals(order)
    write_biz_audit(
        action="order.add_item",
        entity_type="order",
        entity_id=order.order_code,
        note=f"Added {catalog.code}",
    )
    return item


def submit_order_for_payment(order_ref: str, actor: str | None = None) -> BizOrder:
    order = _get_order(order_ref)
    if not order.items:
        raise BusinessEngineError("Order has no items")
    _recalc_order_totals(order)
    return _transition_order(order, ORDER_PAYMENT_PENDING, action="order.submit", actor=actor)


# --- Payment ---


def create_invoice_from_order(order_ref: str, actor: str | None = None) -> BizInvoice:
    order = _get_order(order_ref)
    existing = BizInvoice.query.filter_by(order_id=order.id).first()
    if existing:
        return existing
    invoice = BizInvoice(
        invoice_no=_code("INV"),
        order_id=order.id,
        amount=order.total_amount,
        status=INVOICE_UNPAID,
    )
    db.session.add(invoice)
    db.session.flush()
    write_biz_audit(
        action="invoice.create",
        entity_type="invoice",
        entity_id=invoice.invoice_no,
        new_status=INVOICE_UNPAID,
        note=f"Order {order.order_code}",
        actor=actor,
    )
    return invoice


def mark_order_paid(
    order_ref: str,
    *,
    payment_method: str,
    receipt_number: str | None = None,
    actor: str | None = None,
) -> BizPayment:
    if not payment_method or not payment_method.strip():
        raise BusinessEngineError("payment_method is required")
    order = _get_order(order_ref)
    if order.status not in {ORDER_PAYMENT_PENDING, ORDER_DRAFT}:
        if order.status != ORDER_PAID:
            raise BusinessEngineError(f"Order not payable in status {order.status}")
    invoice = create_invoice_from_order(order.order_code, actor=actor)
    if invoice.status == INVOICE_PAID:
        payment = BizPayment.query.filter_by(invoice_id=invoice.id).first()
        if payment:
            return payment
    receipt = receipt_number or _code("RCT")
    paid_at = _utcnow()
    payment = BizPayment(
        invoice_id=invoice.id,
        order_id=order.id,
        payment_method=payment_method.strip(),
        receipt_number=receipt,
        amount=invoice.amount,
        paid_at=paid_at,
        created_by=actor,
    )
    invoice.status = INVOICE_PAID
    db.session.add(payment)
    db.session.flush()
    if order.status == ORDER_PAYMENT_PENDING:
        _transition_order(order, ORDER_PAID, action="order.mark_paid", note=receipt, actor=actor)
    elif order.status == ORDER_DRAFT:
        _transition_order(order, ORDER_PAYMENT_PENDING, action="order.submit", actor=actor)
        _transition_order(order, ORDER_PAID, action="order.mark_paid", note=receipt, actor=actor)
    if not order.barcode_value and table_has_column("biz_orders", "barcode_value"):
        order.barcode_value = f"BC-{order.order_code}"
    write_biz_audit(
        action="payment.record",
        entity_type="payment",
        entity_id=receipt,
        new_status=INVOICE_PAID,
        note=f"method={payment_method}",
        actor=actor,
    )
    return payment


# --- Collection ---


def create_collection_job(
    order_ref: str,
    *,
    collector_name: str,
    pickup_address: str,
    scheduled_at: datetime | None = None,
    actor: str | None = None,
) -> BizCollection:
    if not collector_name or not collector_name.strip():
        raise BusinessEngineError("collector_name is required")
    if not pickup_address or not pickup_address.strip():
        raise BusinessEngineError("pickup_address is required")
    order = _get_order(order_ref)
    if order.status != ORDER_PAID:
        raise BusinessEngineError("Collection requires paid order")
    existing = BizCollection.query.filter_by(order_id=order.id).first()
    if existing:
        return existing
    sample_code = _code("SMP")
    collection = BizCollection(
        order_id=order.id,
        collector_name=collector_name.strip(),
        pickup_address=pickup_address.strip(),
        scheduled_at=scheduled_at or _utcnow(),
        status=COLLECTION_ASSIGNED,
        sample_code=sample_code,
        barcode_value=f"BC-{sample_code}",
    )
    db.session.add(collection)
    _transition_order(order, ORDER_SAMPLING, action="collection.create", actor=actor)
    write_biz_audit(
        action="collection.create",
        entity_type="collection",
        entity_id=sample_code,
        new_status=COLLECTION_ASSIGNED,
        actor=actor,
    )
    return collection


def accept_collection(order_ref: str, actor: str | None = None) -> BizCollection:
    order = _get_order(order_ref)
    collection = BizCollection.query.filter_by(order_id=order.id).first()
    if not collection:
        raise BusinessEngineError("Collection job not found")
    if collection.status != COLLECTION_ASSIGNED:
        raise BusinessEngineError(f"Cannot accept pickup in status {collection.status}")
    old = collection.status
    collection.status = COLLECTION_ACCEPTED
    collection.updated_at = _utcnow()
    write_biz_audit(
        action="collection.accept",
        entity_type="collection",
        entity_id=collection.sample_code or order.order_code,
        old_status=old,
        new_status=COLLECTION_ACCEPTED,
        actor=actor,
    )
    return collection


def collect_sample(order_ref: str, actor: str | None = None) -> BizCollection:
    order = _get_order(order_ref)
    collection = BizCollection.query.filter_by(order_id=order.id).first()
    if not collection:
        raise BusinessEngineError("Collection job not found")
    if collection.status not in {COLLECTION_ACCEPTED, COLLECTION_ASSIGNED}:
        raise BusinessEngineError(f"Cannot collect sample in status {collection.status}")
    old = collection.status
    collection.status = COLLECTION_COLLECTED
    collection.updated_at = _utcnow()
    _transition_order(order, ORDER_COLLECTED, action="collection.collect", actor=actor)
    write_biz_audit(
        action="collection.collect",
        entity_type="collection",
        entity_id=collection.sample_code or order.order_code,
        old_status=old,
        new_status=COLLECTION_COLLECTED,
        actor=actor,
    )
    return collection


def update_chain_of_custody(
    order_ref: str,
    *,
    custody_note: str,
    actor: str | None = None,
) -> BizCollection:
    if not custody_note or not custody_note.strip():
        raise BusinessEngineError("custody_note is required")
    order = _get_order(order_ref)
    collection = BizCollection.query.filter_by(order_id=order.id).first()
    if not collection:
        raise BusinessEngineError("Collection job not found")
    write_biz_audit(
        action="collection.custody",
        entity_type="collection",
        entity_id=collection.sample_code or order.order_code,
        note=custody_note.strip(),
        actor=actor,
    )
    collection.updated_at = _utcnow()
    return collection


def handover_sample(order_ref: str, actor: str | None = None) -> BizCollection:
    order = _get_order(order_ref)
    collection = BizCollection.query.filter_by(order_id=order.id).first()
    if not collection:
        raise BusinessEngineError("Collection job not found")
    if collection.status != COLLECTION_COLLECTED:
        raise BusinessEngineError(f"Cannot mark in transit in status {collection.status}")
    collection.status = COLLECTION_IN_TRANSIT
    collection.updated_at = _utcnow()
    _transition_order(order, ORDER_IN_TRANSIT, action="collection.in_transit", actor=actor)
    write_biz_audit(
        action="collection.in_transit",
        entity_type="collection",
        entity_id=collection.sample_code or order.order_code,
        new_status=COLLECTION_IN_TRANSIT,
        actor=actor,
    )
    return collection


# --- Lab receive ---


def receive_sample_at_lab(
    order_ref: str,
    *,
    received_by: str,
    accession_number: str | None = None,
    actor: str | None = None,
) -> BizCollection:
    if not received_by or not received_by.strip():
        raise BusinessEngineError("received_by is required")
    order = _get_order(order_ref)
    collection = BizCollection.query.filter_by(order_id=order.id).first()
    if not collection:
        raise BusinessEngineError("Collection job not found")
    collection.received_by = received_by.strip()
    collection.received_at = _utcnow()
    collection.accession_number = accession_number or _code("ACC")
    collection.status = COLLECTION_DELIVERED
    _transition_order(order, ORDER_LAB_RECEIVED, action="lab.receive", actor=actor)
    write_biz_audit(
        action="lab.receive",
        entity_type="collection",
        entity_id=collection.accession_number,
        new_status=ORDER_LAB_RECEIVED,
        note=f"received_by={received_by}",
        actor=actor,
    )
    return collection


# --- Results ---


def _ensure_result(order: BizOrder) -> BizResult:
    result = BizResult.query.filter_by(order_id=order.id).first()
    if result:
        return result
    result = BizResult(result_code=_code("RPT"), order_id=order.id, status=RESULT_TESTING)
    db.session.add(result)
    db.session.flush()
    return result


def enter_results(
    order_ref: str,
    items: list[dict],
    actor: str | None = None,
) -> BizResult:
    order = _get_order(order_ref)
    if order.status not in {ORDER_LAB_RECEIVED, ORDER_TESTING, ORDER_PENDING_REVIEW}:
        if order.status == ORDER_IN_TRANSIT:
            receive_sample_at_lab(order_ref, received_by=actor or "LAB", actor=actor)
            order = _get_order(order_ref)
        else:
            raise BusinessEngineError(f"Cannot enter results in status {order.status}")
    result = _ensure_result(order)
    BizResultItem.query.filter_by(result_id=result.id).delete()
    for idx, item in enumerate(items):
        value = str(item.get("result_value", "")).strip()
        if not value:
            raise BusinessEngineError("result_value is required for each item")
        flag = item.get("flag") or "NORMAL"
        if flag == "NORMAL" and value:
            try:
                numeric = float(re.sub(r"[^\d.]", "", value))
                ref = item.get("reference_range", "")
                if "-" in ref:
                    parts = ref.split("-")
                    low, high = float(parts[0]), float(parts[1])
                    if numeric < low or numeric > high:
                        flag = "ABNORMAL"
            except (ValueError, IndexError):
                pass
        db.session.add(
            BizResultItem(
                result_id=result.id,
                test_code=item.get("test_code"),
                test_name=item.get("test_name") or "Test",
                result_value=value,
                unit=item.get("unit"),
                reference_range=item.get("reference_range"),
                flag=flag,
            )
        )
    result.status = RESULT_TESTING
    if order.status == ORDER_LAB_RECEIVED:
        _transition_order(order, ORDER_TESTING, action="lab.start_testing", actor=actor)
    write_biz_audit(
        action="result.enter",
        entity_type="result",
        entity_id=result.result_code,
        new_status=RESULT_TESTING,
        actor=actor,
    )
    return result


def complete_qc(order_ref: str, actor: str | None = None) -> BizResult:
    order = _get_order(order_ref)
    if order.status != ORDER_TESTING:
        raise BusinessEngineError(f"QC complete requires testing status, got {order.status}")
    result = BizResult.query.filter_by(order_id=order.id).first()
    if not result or not result.items:
        raise BusinessEngineError("No result items to QC")
    result.status = RESULT_PENDING_REVIEW
    _transition_order(order, ORDER_PENDING_REVIEW, action="lab.qc_complete", actor=actor)
    write_biz_audit(
        action="lab.qc_complete",
        entity_type="result",
        entity_id=result.result_code,
        new_status=RESULT_PENDING_REVIEW,
        actor=actor,
    )
    return result


def approve_result(order_ref: str, *, doctor_note: str | None = None, actor: str | None = None) -> BizResult:
    order = _get_order(order_ref)
    result = BizResult.query.filter_by(order_id=order.id).first()
    if not result:
        raise BusinessEngineError("Result not found")
    result.doctor_note = doctor_note
    result.approved_at = _utcnow()
    result.approved_by = actor
    result.status = RESULT_APPROVED
    _transition_order(order, ORDER_APPROVED, action="result.approve", note=doctor_note, actor=actor)
    write_biz_audit(
        action="result.approve",
        entity_type="result",
        entity_id=result.result_code,
        new_status=RESULT_APPROVED,
        note=doctor_note,
        actor=actor,
    )
    return result


def release_report(order_ref: str, actor: str | None = None) -> BizResult:
    order = _get_order(order_ref)
    result = BizResult.query.filter_by(order_id=order.id).first()
    if not result:
        raise BusinessEngineError("Result not found")
    result.released_at = _utcnow()
    result.status = RESULT_RELEASED
    result.patient_visible = True
    result.html_content = render_report_html(result, order)
    _transition_order(order, ORDER_RELEASED, action="result.release", actor=actor)
    write_biz_audit(
        action="result.release",
        entity_type="result",
        entity_id=result.result_code,
        new_status=RESULT_RELEASED,
        actor=actor,
    )
    return result


def render_report_html(result: BizResult, order: BizOrder) -> str:
    rows = []
    for item in result.items:
        rows.append(
            f"<tr><td>{item.test_name}</td><td>{item.result_value} {item.unit or ''}</td>"
            f"<td>{item.reference_range or '—'}</td><td>{item.flag}</td></tr>"
        )
    return (
        f"<html><body><h1>DxCon Diagnostic Report</h1>"
        f"<p>Order: {order.order_code} · Patient: {order.patient_name}</p>"
        f"<p>Released: {result.released_at}</p>"
        f"<table border='1' cellpadding='6'><tr><th>Test</th><th>Result</th><th>Reference</th><th>Flag</th></tr>"
        f"{''.join(rows)}</table>"
        f"<p><em>Clinician note: {result.doctor_note or '—'}</em></p></body></html>"
    )


def render_request_form_html(order: BizOrder) -> str:
    tests = "".join(
        f"<li>{item.test_name} ({item.test_code}) — ${item.line_total:,.0f}</li>"
        for item in order.items
    )
    barcode = order.barcode_value or "—"
    return (
        f"<html><body><h1>Lab Request Form</h1>"
        f"<p>Order: {order.order_code}</p>"
        f"<p>Patient: {order.patient_name} ({order.patient_code})</p>"
        f"<p>Barcode: {barcode}</p>"
        f"<ul>{tests}</ul>"
        f"<p>Total: ${order.total_amount:,.0f}</p>"
        f"<p><em>Generated by DxCon business engine</em></p></body></html>"
    )


# --- Queries ---


def list_orders(limit: int = 20) -> list[BizOrder]:
    return BizOrder.query.order_by(BizOrder.created_at.desc()).limit(limit).all()


def order_to_detail(order_ref: str) -> dict:
    order = _get_order(order_ref)
    invoice = BizInvoice.query.filter_by(order_id=order.id).first()
    collection = BizCollection.query.filter_by(order_id=order.id).first()
    result = BizResult.query.filter_by(order_id=order.id).first()
    audits = (
        BizWorkflowAudit.query.filter_by(entity_type="order", entity_id=order.order_code)
        .order_by(BizWorkflowAudit.created_at.asc())
        .all()
    )
    timeline = [
        {
            "label": a.action.replace(".", " ").title(),
            "status": a.new_status or "—",
            "time": a.created_at.strftime("%H:%M") if a.created_at else "—",
        }
        for a in audits
    ]
    return {
        **order.to_dict(),
        "invoice": invoice.to_dict() if invoice else None,
        "collection": collection.to_dict() if collection else None,
        "result": result.to_dict() if result else None,
        "timeline": timeline,
    }


def result_to_detail(result_ref: str) -> dict:
    result = BizResult.query.filter(
        or_(BizResult.result_code == result_ref, BizResult.id == result_ref)
    ).first()
    if not result:
        raise BusinessEngineError("Result not found")
    order = BizOrder.query.get(result.order_id)
    first_item = result.items[0] if result.items else None
    return {
        "id": result.result_code,
        "result_code": result.result_code,
        "order_code": order.order_code if order else "",
        "patient_name": order.patient_name if order else "",
        "test_name": first_item.test_name if first_item else "Panel",
        "result_value": first_item.result_value if first_item else "",
        "unit": first_item.unit if first_item else "",
        "reference_range": first_item.reference_range if first_item else "",
        "flag": first_item.flag if first_item else "NORMAL",
        "approval_status": result.status,
        "interpretation": result.doctor_note or "Results within expected clinical range.",
        "html_content": result.html_content,
        "items": [i.to_dict() for i in result.items],
        "released_at": result.released_at.isoformat() if result.released_at else None,
    }


def finance_summary() -> dict:
    invoices = BizInvoice.query.all()
    paid = [i for i in invoices if i.status == INVOICE_PAID]
    pending = [i for i in invoices if i.status != INVOICE_PAID]
    revenue = sum(i.amount for i in paid)
    return {
        "revenue": revenue,
        "paid_count": len(paid),
        "pending_count": len(pending),
        "invoice_total": len(invoices),
    }


def list_invoices(limit: int = 20) -> list[dict]:
    rows = []
    for invoice in BizInvoice.query.order_by(BizInvoice.created_at.desc()).limit(limit).all():
        order = BizOrder.query.get(invoice.order_id)
        payment = BizPayment.query.filter_by(invoice_id=invoice.id).first()
        rows.append({
            "invoice_no": invoice.invoice_no,
            "amount": invoice.amount,
            "status": invoice.status.upper(),
            "order_code": order.order_code if order else "",
            "payment_method": payment.payment_method if payment else "—",
        })
    return rows


def list_collections(limit: int = 20) -> list[dict]:
    rows = []
    for collection in BizCollection.query.order_by(BizCollection.created_at.desc()).limit(limit).all():
        order = BizOrder.query.get(collection.order_id)
        rows.append({
            **collection.to_dict(),
            "order_code": order.order_code if order else "",
            "patient_name": order.patient_name if order else "",
        })
    return rows


def list_reports(limit: int = 20) -> list[dict]:
    rows = []
    for result in BizResult.query.order_by(BizResult.created_at.desc()).limit(limit).all():
        detail = result_to_detail(result.result_code)
        rows.append({
            "id": result.result_code,
            "test_name": detail["test_name"],
            "patient_name": detail["patient_name"],
            "approval_status": result.status,
            "flag": detail["flag"],
        })
    return rows


def list_collector_assignments(collector_name: str | None = None, limit: int = 20) -> list[dict]:
    query = BizCollection.query
    if collector_name:
        query = query.filter(BizCollection.collector_name == collector_name.strip())
    rows = []
    for collection in query.order_by(BizCollection.created_at.desc()).limit(limit).all():
        order = BizOrder.query.get(collection.order_id)
        rows.append({
            **collection.to_dict(),
            "order_code": order.order_code if order else "",
            "patient_name": order.patient_name if order else "",
            "patient_code": order.patient_code if order else "",
            "order_status": order.status if order else "",
        })
    return rows


def list_lab_incoming(limit: int = 20) -> list[dict]:
    statuses = {ORDER_IN_TRANSIT, ORDER_LAB_RECEIVED, ORDER_TESTING}
    rows = []
    for order in BizOrder.query.filter(BizOrder.status.in_(statuses)).order_by(BizOrder.updated_at.desc()).limit(limit):
        collection = BizCollection.query.filter_by(order_id=order.id).first()
        rows.append({
            "order_code": order.order_code,
            "patient_name": order.patient_name,
            "status": order.status,
            "accession_number": collection.accession_number if collection else None,
            "sample_code": collection.sample_code if collection else None,
        })
    return rows


def list_pending_doctor_reviews(limit: int = 20) -> list[dict]:
    rows = []
    for result in BizResult.query.filter_by(status=RESULT_PENDING_REVIEW).order_by(BizResult.created_at.desc()).limit(limit):
        detail = result_to_detail(result.result_code)
        rows.append({
            "id": result.result_code,
            "result_code": result.result_code,
            "order_code": detail["order_code"],
            "patient_name": detail["patient_name"],
            "test_name": detail["test_name"],
            "flag": detail["flag"],
            "approval_status": result.status,
        })
    return rows


def get_patient_portal_data(patient_code: str) -> dict:
    patient = Patient.query.get(patient_code)
    if not patient:
        raise BusinessEngineError("Patient not found")
    profile = PatientProfile.query.filter_by(patient_id=patient_code).first()
    orders = BizOrder.query.filter_by(patient_code=patient_code).order_by(BizOrder.created_at.desc()).all()
    invoices = []
    released_reports = []
    unreleased_count = 0
    for order in orders:
        inv = BizInvoice.query.filter_by(order_id=order.id).first()
        if inv:
            payment = BizPayment.query.filter_by(invoice_id=inv.id).first()
            invoices.append({
                **inv.to_dict(),
                "order_code": order.order_code,
                "payment_method": payment.payment_method if payment else None,
            })
        res = BizResult.query.filter_by(order_id=order.id).first()
        if res:
            if res.status == RESULT_RELEASED and res.patient_visible:
                released_reports.append({
                    **res.to_dict(include_items=False),
                    "order_code": order.order_code,
                    "html_content": res.html_content,
                })
            elif res.status != RESULT_RELEASED:
                unreleased_count += 1
    try:
        from app.reporting_engine.service import patient_released_reports

        clinical = patient_released_reports(patient_code)
        seen = {r.get("report_code") or r.get("result_code") for r in released_reports}
        for cr in clinical:
            if cr.get("report_code") not in seen:
                released_reports.append({**cr, "order_code": cr.get("order_code")})
    except Exception:
        pass
    return {
        "patient": patient.to_dict(),
        "qr_payload": profile.qr_payload if profile else _qr_payload(patient_code),
        "orders": [o.to_dict(include_items=False) for o in orders],
        "invoices": invoices,
        "released_reports": released_reports,
        "unreleased_report_count": unreleased_count,
    }


def ensure_test_catalog_seed() -> list[TestCatalog]:
    if TestCatalog.query.count():
        return TestCatalog.query.limit(5).all()
    samples = [
        ("CBC", "Complete Blood Count", "Hematology", "Blood", 150000),
        ("GLU", "Glucose Fasting", "Chemistry", "Serum", 80000),
        ("LIPID", "Lipid Panel", "Chemistry", "Serum", 220000),
    ]
    created = []
    for code, name, category, sample_type, price in samples:
        item = TestCatalog(code=code, name=name, category=category, sample_type=sample_type, price=price)
        db.session.add(item)
        created.append(item)
    db.session.flush()
    return created


def audit_count_for_entity(entity_type: str, entity_id: str) -> int:
    return BizWorkflowAudit.query.filter_by(entity_type=entity_type, entity_id=entity_id).count()
