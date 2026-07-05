"""Reception operational workspace service — orchestrates business engine + queue."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import or_

from app.business_engine import service as biz
from app.business_engine.service import BusinessEngineError
from app.extensions.db import db
from app.models.biz_order import BizCollection, BizInvoice, BizOrder, BizPayment
from app.models.patient import Patient
from app.models.patient_profile import PatientProfile
from app.models.reception_queue_entry import ReceptionQueueEntry
from app.models.test_catalog import TestCatalog
from app.reception_workspace.audit import log_reception_activity, write_reception_audit
from app.services import reception_service
from app.services.reception_service import (
    STATUS_CHECKED_IN,
    STATUS_WAITING,
    dashboard_payload,
    get_kpis,
    serialize_queue,
    today_queue_entries,
)
from app.business_engine.statuses import COLLECTION_ASSIGNED, ORDER_PAID, ORDER_PAYMENT_PENDING

WORKFLOW_WAITING = "WAITING"
WORKFLOW_CHECKED_IN = "CHECKED_IN"
WORKFLOW_PAYMENT_PENDING = "PAYMENT_PENDING"
WORKFLOW_PAID = "PAID"
WORKFLOW_SAMPLING = "SAMPLING"
WORKFLOW_COMPLETED = "COMPLETED"
WORKFLOW_CANCELLED = "CANCELLED"

PAYMENT_METHODS = ("cash", "transfer", "qr", "pos", "corporate", "insurance")
PAYMENT_STATUSES = ("paid", "pending", "partial", "waived")


class ReceptionWorkspaceError(ValueError):
    pass


def duplicate_warnings(*, phone: str | None = None, national_id: str | None = None) -> list[dict]:
    warnings: list[dict] = []
    if phone and phone.strip():
        existing = Patient.query.filter_by(phone=phone.strip()).first()
        if existing:
            warnings.append({"field": "phone", "message": f"Phone already registered to {existing.full_name}", "patient_code": existing.patient_code})
    if national_id and national_id.strip():
        existing = Patient.query.filter_by(national_id=national_id.strip()).first()
        if existing:
            warnings.append({"field": "national_id", "message": f"National ID already registered to {existing.full_name}", "patient_code": existing.patient_code})
    return warnings


def fast_search_patients(
    query: str,
    *,
    limit: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    q = (query or "").strip()
    if not q:
        rows = Patient.query.order_by(Patient.created_at.desc()).limit(limit).offset((page - 1) * limit).all()
        total = Patient.query.count()
        return {"data": [_patient_search_row(p) for p in rows], "pagination": {"page": page, "per_page": limit, "total": total}}

    if q.lower().startswith("dxcon:patient:"):
        q = q.split(":")[-1]

    pattern = f"%{q}%"
    base = Patient.query.filter(
        or_(
            Patient.patient_code.ilike(pattern),
            Patient.full_name.ilike(pattern),
            Patient.phone.ilike(pattern),
            Patient.national_id.ilike(pattern),
        )
    )
    total = base.count()
    rows = base.order_by(Patient.full_name).offset((page - 1) * limit).limit(limit).all()
    return {"data": [_patient_search_row(p) for p in rows], "pagination": {"page": page, "per_page": limit, "total": total}}


def _patient_search_row(patient: Patient) -> dict:
    profile = PatientProfile.query.filter_by(patient_id=patient.patient_code).first()
    return {
        **patient.to_dict(),
        "qr_payload": profile.qr_payload if profile else f"dxcon:patient:{patient.patient_code}",
    }


def register_patient(
    data: dict[str, Any],
    *,
    actor: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    warnings = duplicate_warnings(phone=data.get("phone"), national_id=data.get("national_id"))
    if warnings and not force:
        return {"ok": False, "warnings": warnings, "duplicate": True}

    patient = biz.create_patient(
        full_name=data.get("full_name", ""),
        phone=data.get("phone"),
        email=data.get("email"),
        gender=data.get("gender"),
        date_of_birth=data.get("date_of_birth"),
        address=data.get("address"),
        national_id=data.get("national_id"),
        actor=actor,
    )
    queue_entry = reception_service.create_queue_entry(
        patient.patient_code,
        visit_type="WALK_IN",
        actor_email=actor,
    )
    queue_entry.workflow_status = WORKFLOW_WAITING
    write_reception_audit(action="patient_created", object_type="patient", object_id=patient.patient_code, actor=actor)
    log_reception_activity("PATIENT_REGISTERED", patient_id=patient.patient_code, queue_entry_id=queue_entry.id, actor=actor)
    profile = PatientProfile.query.filter_by(patient_id=patient.patient_code).first()
    return {
        "ok": True,
        "patient": _patient_search_row(patient),
        "queue_entry": queue_entry.to_dict(),
        "qr_payload": profile.qr_payload if profile else f"dxcon:patient:{patient.patient_code}",
        "warnings": warnings,
    }


def get_patient_profile(patient_code: str) -> dict[str, Any]:
    patient = Patient.query.get(patient_code)
    if not patient:
        raise ReceptionWorkspaceError("Patient not found")
    detail = biz.patient_to_detail(patient)
    detail["notes"] = []
    detail["medical_history"] = []
    detail["quick_actions"] = ["new_order", "edit", "print_patient_card"]
    return detail


def search_tests(
    *,
    query: str | None = None,
    category: str | None = None,
    department: str | None = None,
    limit: int = 50,
    page: int = 1,
) -> dict[str, Any]:
    biz.ensure_test_catalog_seed()
    q = TestCatalog.query
    if query:
        term = f"%{query.strip()}%"
        q = q.filter(or_(TestCatalog.code.ilike(term), TestCatalog.name.ilike(term), TestCatalog.category.ilike(term)))
    if category:
        q = q.filter(TestCatalog.category.ilike(f"%{category}%"))
    if department:
        q = q.filter(TestCatalog.category.ilike(f"%{department}%"))
    total = q.count()
    rows = q.order_by(TestCatalog.name).offset((page - 1) * limit).limit(limit).all()
    return {
        "data": [
            {
                **t.to_dict(),
                "sample_type": t.sample_type,
                "turnaround_hours": getattr(t, "turnaround_hours", None),
                "price_display": t.price or 0,
            }
            for t in rows
        ],
        "pagination": {"page": page, "per_page": limit, "total": total},
    }


def create_reception_order(
    *,
    patient_code: str,
    test_catalog_ids: list[str],
    discount: float = 0,
    note: str | None = None,
    queue_entry_id: str | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    if not test_catalog_ids:
        raise ReceptionWorkspaceError("At least one test is required")
    order = biz.create_order(
        patient_code=patient_code,
        test_catalog_ids=test_catalog_ids,
        discount=discount,
        note=note,
        actor=actor,
    )
    biz.submit_order_for_payment(order.order_code, actor=actor)
    invoice = biz.create_invoice_from_order(order.order_code, actor=actor)
    if queue_entry_id:
        entry = ReceptionQueueEntry.query.get(queue_entry_id)
        if entry:
            entry.order_id = order.id
            entry.invoice_id = invoice.id
            entry.payment_status = "PENDING"
            entry.workflow_status = WORKFLOW_PAYMENT_PENDING
    else:
        entry = _find_or_create_queue_for_patient(patient_code, actor=actor)
        if entry:
            entry.order_id = order.id
            entry.invoice_id = invoice.id
            entry.workflow_status = WORKFLOW_PAYMENT_PENDING
    write_reception_audit(action="order_created", object_type="order", object_id=order.order_code, actor=actor)
    return {
        "order": biz.order_to_detail(order.order_code),
        "invoice": invoice.to_dict(),
        "pricing": {"subtotal": order.subtotal, "discount": order.discount, "total": order.total_amount},
    }


def collect_payment(
    order_ref: str,
    *,
    payment_method: str = "cash",
    receipt_number: str | None = None,
    amount: float | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    if payment_method.lower() not in PAYMENT_METHODS:
        raise ReceptionWorkspaceError(f"Invalid payment method: {payment_method}")
    payment = biz.mark_order_paid(
        order_ref,
        payment_method=payment_method,
        receipt_number=receipt_number,
        actor=actor,
    )
    order = BizOrder.query.filter(
        or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)
    ).first()
    invoice = BizInvoice.query.filter_by(order_id=order.id).first() if order else None
    _sync_queue_after_payment(order, invoice, actor=actor)
    write_reception_audit(action="payment_collected", object_type="payment", object_id=payment.receipt_number, actor=actor)
    barcodes = generate_barcodes(order.order_code) if order else {}
    return {
        "payment": payment.to_dict(),
        "invoice": invoice.to_dict() if invoice else None,
        "order_status": order.status if order else None,
        "barcodes": barcodes,
    }


def _sync_queue_after_payment(order: BizOrder | None, invoice: BizInvoice | None, *, actor: str | None = None) -> None:
    if not order:
        return
    entry = ReceptionQueueEntry.query.filter_by(order_id=order.id).first()
    if not entry:
        entry = ReceptionQueueEntry.query.filter_by(patient_id=order.patient_code, queue_date=datetime.utcnow().date()).order_by(
            ReceptionQueueEntry.created_at.desc()
        ).first()
    if entry:
        entry.payment_status = "PAID"
        entry.workflow_status = WORKFLOW_PAID
        if invoice:
            entry.invoice_id = invoice.id
        log_reception_activity("PAYMENT_COLLECTED", patient_id=order.patient_code, queue_entry_id=entry.id, actor=actor)


def create_collection_after_payment(
    order_ref: str,
    *,
    collector_name: str = "Walk-in Collector",
    pickup_address: str = "Reception Desk",
    actor: str | None = None,
) -> dict[str, Any]:
    collection = biz.create_collection_job(
        order_ref,
        collector_name=collector_name,
        pickup_address=pickup_address,
        actor=actor,
    )
    order = BizOrder.query.filter(or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)).first()
    entry = ReceptionQueueEntry.query.filter_by(order_id=order.id).first() if order else None
    if entry:
        entry.workflow_status = WORKFLOW_SAMPLING
    write_reception_audit(action="collection_created", object_type="collection", object_id=collection.id, actor=actor)
    return {"collection": collection.to_dict(), "queue_entry": entry.to_dict() if entry else None}


def generate_barcodes(order_ref: str) -> dict[str, Any]:
    order = BizOrder.query.filter(or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")
    patient = Patient.query.get(order.patient_code)
    collection = BizCollection.query.filter_by(order_id=order.id).first()
    samples = []
    for item in order.items:
        sample_code = f"SMP-{item.test_code}-{order.order_code}"
        samples.append({
            "test_code": item.test_code,
            "test_name": item.test_name,
            "sample_type": item.test_name,
            "barcode": f"BC-{sample_code}",
        })
    payload = {
        "order_barcode": order.barcode_value or f"BC-{order.order_code}",
        "patient_barcode": f"BC-PAT-{order.patient_code}",
        "patient_qr": f"dxcon:patient:{order.patient_code}",
        "sample_barcodes": samples,
        "collection_barcode": collection.barcode_value if collection else None,
    }
    write_reception_audit(action="barcode_printed", object_type="order", object_id=order.order_code)
    return payload


def render_request_form(order_ref: str) -> str:
    order = BizOrder.query.filter(or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")
    write_reception_audit(action="request_form_printed", object_type="order", object_id=order.order_code)
    return biz.render_request_form_html(order)


def workspace_dashboard() -> dict[str, Any]:
    base = dashboard_payload()
    kpis = get_kpis()
    orders_pending_payment = BizOrder.query.filter(BizOrder.status == ORDER_PAYMENT_PENDING).count()
    orders_waiting_collection = BizCollection.query.filter(BizCollection.status == COLLECTION_ASSIGNED).count()
    recent_orders = [
        o.to_dict(include_items=False)
        for o in BizOrder.query.order_by(BizOrder.created_at.desc()).limit(10).all()
    ]
    recent_patients = [
        _patient_search_row(p)
        for p in Patient.query.order_by(Patient.created_at.desc()).limit(10).all()
    ]
    queue_all = today_queue_entries()
    patients_by_code = {p.patient_code: p for p in Patient.query.filter(Patient.patient_code.in_([e.patient_id for e in queue_all] or [""])).all()}
    workflow_queue = [serialize_queue(e, patients_by_code) for e in queue_all]
    for row in workflow_queue:
        row["workflow_status"] = row.get("workflow_status") or _derive_workflow(row)
    return {
        **base,
        "kpis": {
            **kpis,
            "todays_revenue": _todays_revenue(),
            "pending_payments": max(kpis.get("pending_payment", 0), orders_pending_payment),
            "waiting_collections": orders_waiting_collection,
        },
        "widgets": [
            "todays_queue", "waiting_patients", "check_in", "new_registration",
            "orders_waiting_payment", "orders_waiting_collection", "quick_search",
            "recent_patients", "recent_orders", "notifications",
        ],
        "workflow_queue": workflow_queue,
        "recent_orders": recent_orders,
        "recent_patients": recent_patients,
        "orders_waiting_payment": [
            o.to_dict(include_items=False)
            for o in BizOrder.query.filter(BizOrder.status == ORDER_PAYMENT_PENDING).limit(20).all()
        ],
        "orders_waiting_collection": [
            c.to_dict()
            for c in BizCollection.query.filter(BizCollection.status == COLLECTION_ASSIGNED).limit(20).all()
        ],
    }


def _derive_workflow(row: dict) -> str:
    ps = (row.get("payment_status") or "").upper()
    st = (row.get("status") or "").upper()
    if ps == "PAID":
        return WORKFLOW_PAID
    if ps == "PENDING":
        return WORKFLOW_PAYMENT_PENDING
    if st == STATUS_CHECKED_IN:
        return WORKFLOW_CHECKED_IN
    if st == "CHECKED_OUT":
        return WORKFLOW_COMPLETED
    return WORKFLOW_WAITING


def _todays_revenue() -> float:
    today = datetime.utcnow().date()
    payments = BizPayment.query.filter(BizPayment.paid_at >= datetime.combine(today, datetime.min.time())).all()
    return round(sum(p.amount or 0 for p in payments), 2)


def _find_or_create_queue_for_patient(patient_code: str, *, actor: str | None = None) -> ReceptionQueueEntry | None:
    today = datetime.utcnow().date()
    entry = (
        ReceptionQueueEntry.query.filter_by(patient_id=patient_code, queue_date=today)
        .order_by(ReceptionQueueEntry.created_at.desc())
        .first()
    )
    if entry:
        return entry
    try:
        return reception_service.create_queue_entry(patient_code, visit_type="WALK_IN", actor_email=actor)
    except Exception:
        return None


def reception_workspace_report() -> dict[str, Any]:
    return {
        "report": "RECEPTION_WORKSPACE_REPORT",
        "queue_entries_today": len(today_queue_entries()),
        "patients_total": Patient.query.count(),
        "orders_total": BizOrder.query.count(),
        "dashboard_widgets": 10,
    }


def payment_report() -> dict[str, Any]:
    return {
        "report": "PAYMENT_REPORT",
        "methods": list(PAYMENT_METHODS),
        "statuses": list(PAYMENT_STATUSES),
        "payments_today": BizPayment.query.filter(
            BizPayment.paid_at >= datetime.combine(datetime.utcnow().date(), datetime.min.time())
        ).count(),
        "pending_orders": BizOrder.query.filter_by(status=ORDER_PAYMENT_PENDING).count(),
    }


def queue_report() -> dict[str, Any]:
    entries = today_queue_entries()
    by_status: dict[str, int] = {}
    for e in entries:
        ws = e.workflow_status or WORKFLOW_WAITING
        by_status[ws] = by_status.get(ws, 0) + 1
    return {
        "report": "QUEUE_REPORT",
        "total_today": len(entries),
        "by_workflow_status": by_status,
        "statuses": [
            WORKFLOW_WAITING, WORKFLOW_CHECKED_IN, WORKFLOW_PAYMENT_PENDING,
            WORKFLOW_PAID, WORKFLOW_SAMPLING, WORKFLOW_COMPLETED, WORKFLOW_CANCELLED,
        ],
    }
