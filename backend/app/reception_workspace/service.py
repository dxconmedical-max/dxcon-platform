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
from app.business_engine.statuses import (
    COLLECTION_ASSIGNED,
    COLLECTION_DELIVERED,
    ORDER_COLLECTED,
    ORDER_IN_TRANSIT,
    ORDER_LAB_RECEIVED,
    ORDER_PAID,
    ORDER_PAYMENT_PENDING,
    ORDER_SAMPLING,
    ORDER_TESTING,
)

WORKFLOW_WAITING = "WAITING"
WORKFLOW_CHECKED_IN = "CHECKED_IN"
WORKFLOW_PAYMENT_PENDING = "PAYMENT_PENDING"
WORKFLOW_PAID = "PAID"
WORKFLOW_SAMPLING = "SAMPLING"
WORKFLOW_COMPLETED = "COMPLETED"
WORKFLOW_CANCELLED = "CANCELLED"

PAYMENT_METHODS = ("cash", "transfer", "qr", "pos", "corporate", "insurance")
PAYMENT_STATUSES = ("paid", "pending", "partial", "waived")

# Order already visible on laboratory incoming / past receive.
_LAB_HANDED_OFF_STATUSES = frozenset(
    {
        ORDER_LAB_RECEIVED,
        ORDER_TESTING,
        "pending_review",
        "approved",
        "released",
    }
)


class ReceptionWorkspaceError(ValueError):
    pass


def _collection_is_lab_received(collection: BizCollection | None) -> bool:
    if not collection:
        return False
    return bool(collection.accession_number) or collection.status == COLLECTION_DELIVERED


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
        patient_code=(str(data["patient_code"]).strip() if data.get("patient_code") else None),
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


def payment_summary_for_order(order: BizOrder) -> dict[str, Any]:
    payments = BizPayment.query.filter_by(order_id=order.id).all()
    paid_amount = round(sum(float(p.amount or 0) for p in payments), 2)
    order_total = round(float(order.total_amount or 0), 2)
    outstanding_amount = round(max(0.0, order_total - paid_amount), 2)
    if paid_amount <= 0:
        status = "unpaid"
    elif outstanding_amount <= 0 or order.status == ORDER_PAID:
        status = "paid"
    else:
        status = "partial"
    return {
        "order_total": order_total,
        "paid_amount": paid_amount,
        "outstanding_amount": outstanding_amount,
        "discount": round(float(order.discount or 0), 2),
        "subtotal": round(float(order.subtotal or 0), 2),
        "tax": None,
        "status": status,
        "payment_methods_supported": list(PAYMENT_METHODS),
        "partial_payments_supported": False,
    }


def get_order_with_payment(order_ref: str) -> dict[str, Any]:
    detail = biz.order_to_detail(order_ref)
    order = BizOrder.query.filter(
        or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)
    ).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")
    payment = (
        BizPayment.query.filter_by(order_id=order.id)
        .order_by(BizPayment.paid_at.desc())
        .first()
    )
    invoice = BizInvoice.query.filter_by(order_id=order.id).first()
    summary = payment_summary_for_order(order)
    return {
        "order": detail,
        "pricing": {
            "subtotal": summary["subtotal"],
            "discount": summary["discount"],
            "total": summary["order_total"],
            "tax": summary["tax"],
        },
        "payment_summary": summary,
        "payment": payment.to_dict() if payment else None,
        "invoice": invoice.to_dict() if invoice else None,
    }


def _payment_collect_result(
    order: BizOrder,
    payment: BizPayment,
    *,
    idempotent_replay: bool,
) -> dict[str, Any]:
    invoice = BizInvoice.query.filter_by(order_id=order.id).first()
    db.session.refresh(order)
    return {
        "payment": payment.to_dict(),
        "invoice": invoice.to_dict() if invoice else None,
        "order_status": order.status,
        "payment_summary": payment_summary_for_order(order),
        "idempotent_replay": idempotent_replay,
    }


def collect_payment(
    order_ref: str,
    *,
    payment_method: str = "cash",
    receipt_number: str | None = None,
    amount: float | None = None,
    idempotency_key: str | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    method = (payment_method or "").strip().lower()
    if method not in PAYMENT_METHODS:
        raise ReceptionWorkspaceError(f"Invalid payment method: {payment_method}")

    order = BizOrder.query.filter(
        or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)
    ).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")

    key = (idempotency_key or "").strip() or None
    receipt = (receipt_number or "").strip() or key

    if key:
        existing_by_key = BizPayment.query.filter_by(
            order_id=order.id, receipt_number=key
        ).first()
        if existing_by_key:
            return _payment_collect_result(order, existing_by_key, idempotent_replay=True)

    summary = payment_summary_for_order(order)
    if summary["status"] == "paid" or order.status == ORDER_PAID:
        existing = (
            BizPayment.query.filter_by(order_id=order.id)
            .order_by(BizPayment.paid_at.desc())
            .first()
        )
        if existing:
            return _payment_collect_result(order, existing, idempotent_replay=True)

    outstanding = float(summary["outstanding_amount"])
    pay_amount = float(amount) if amount is not None else outstanding
    if pay_amount <= 0:
        raise ReceptionWorkspaceError("Payment amount must be greater than zero")
    if pay_amount > outstanding + 0.009:
        raise ReceptionWorkspaceError(
            f"Overpayment is not allowed (outstanding={outstanding})"
        )
    if pay_amount < outstanding - 0.009:
        raise ReceptionWorkspaceError(
            "Partial payments are not supported. Collect the full outstanding amount."
        )

    payment = biz.mark_order_paid(
        order_ref,
        payment_method=method,
        receipt_number=receipt,
        actor=actor,
    )
    invoice = BizInvoice.query.filter_by(order_id=order.id).first()
    _sync_queue_after_payment(order, invoice, actor=actor)
    write_reception_audit(
        action="payment_collected",
        object_type="payment",
        object_id=payment.receipt_number,
        actor=actor,
    )
    db.session.refresh(order)
    return _payment_collect_result(order, payment, idempotent_replay=False)


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
    """Create collection job after payment (paid → sampling). Prefer handoff_to_laboratory for M4."""
    collection = biz.create_collection_job(
        order_ref,
        collector_name=collector_name,
        pickup_address=pickup_address,
        actor=actor,
    )
    order = BizOrder.query.filter(
        or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)
    ).first()
    entry = ReceptionQueueEntry.query.filter_by(order_id=order.id).first() if order else None
    if entry:
        entry.workflow_status = WORKFLOW_SAMPLING
    write_reception_audit(
        action="collection_created",
        object_type="collection",
        object_id=collection.id,
        actor=actor,
    )
    return {
        "collection": collection.to_dict(),
        "queue_entry": entry.to_dict() if entry else None,
    }


def handoff_to_laboratory(
    order_ref: str,
    *,
    collector_name: str = "Reception Desk",
    pickup_address: str = "Reception Desk",
    laboratory_name: str = "Central Laboratory",
    laboratory_id: str | None = None,
    actor: str | None = None,
    desk_complete: bool = True,
) -> dict[str, Any]:
    """
    Milestone 4 — paid + documented order → laboratory queue (single insertion).

    Transition path (walk-in desk):
      paid → sampling (collection) → collected → in_transit → lab_received

    Idempotent: if already handed off / collection exists at target, returns existing
    without creating a second queue row.
    """
    order = BizOrder.query.filter(
        or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)
    ).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")

    status = (order.status or "").lower()
    if status in {"cancelled", "canceled", "void"}:
        raise ReceptionWorkspaceError(
            f"Cannot hand off order in status {order.status}"
        )

    summary = payment_summary_for_order(order)
    paid_or_beyond = summary["status"] == "paid" or status in {
        ORDER_PAID,
        ORDER_SAMPLING,
        ORDER_COLLECTED,
        ORDER_IN_TRANSIT,
        *_LAB_HANDED_OFF_STATUSES,
    }
    if not paid_or_beyond:
        raise ReceptionWorkspaceError(
            "Order must be paid before laboratory handoff"
        )

    # Require specimen identifiers + requisition readiness (stable backend codes).
    try:
        barcodes = generate_barcodes(order.order_code)
    except ReceptionWorkspaceError as exc:
        raise ReceptionWorkspaceError(
            f"Specimen identifiers required before handoff: {exc}"
        ) from exc
    if not barcodes.get("order_barcode") or not barcodes.get("sample_barcodes"):
        raise ReceptionWorkspaceError(
            "Specimen barcodes are missing; generate barcode/QR before handoff"
        )
    try:
        requisition = render_request_form(order.order_code)
    except ReceptionWorkspaceError as exc:
        raise ReceptionWorkspaceError(
            f"Requisition required before handoff: {exc}"
        ) from exc
    if not (requisition.get("html") or "").strip():
        raise ReceptionWorkspaceError("Requisition HTML is empty; cannot hand off")

    existing = BizCollection.query.filter_by(order_id=order.id).first()
    if order.status in _LAB_HANDED_OFF_STATUSES or _collection_is_lab_received(existing):
        entry = ReceptionQueueEntry.query.filter_by(order_id=order.id).first()
        if entry:
            entry.workflow_status = WORKFLOW_SAMPLING
        return _handoff_payload(
            order,
            existing,
            barcodes=barcodes,
            laboratory_name=laboratory_name,
            laboratory_id=laboratory_id,
            idempotent_replay=True,
            actor=actor,
        )

    idempotent_replay = False
    collection = existing
    try:
        # create_collection_job requires paid; resume from an existing collection
        # (e.g. create_collection_after_payment) without re-calling it.
        # Do not session.refresh() mid-flow — that can reload pre-flush status.
        if collection is None:
            if order.status != ORDER_PAID:
                raise ReceptionWorkspaceError(
                    f"Cannot create collection for order in status {order.status}"
                )
            collection = biz.create_collection_job(
                order.order_code,
                collector_name=collector_name,
                pickup_address=pickup_address,
                actor=actor,
            )
        else:
            collection = existing

        if desk_complete and collection:
            # Advance walk-in desk sample into the laboratory incoming/received queue once.
            if order.status == ORDER_SAMPLING:
                collection = biz.collect_sample(order.order_code, actor=actor)
            if order.status == ORDER_COLLECTED:
                collection = biz.handover_sample(order.order_code, actor=actor)
            if order.status == ORDER_IN_TRANSIT:
                collection = biz.receive_sample_at_lab(
                    order.order_code,
                    received_by=actor or laboratory_name,
                    actor=actor,
                )
    except BusinessEngineError as exc:
        raise ReceptionWorkspaceError(str(exc)) from exc

    entry = ReceptionQueueEntry.query.filter_by(order_id=order.id).first()
    if entry:
        entry.workflow_status = WORKFLOW_SAMPLING

    write_reception_audit(
        action="lab_handoff",
        object_type="order",
        object_id=order.order_code,
        actor=actor,
    )
    log_reception_activity(
        "LAB_HANDOFF",
        patient_id=order.patient_code,
        queue_entry_id=entry.id if entry else None,
        actor=actor,
    )

    return _handoff_payload(
        order,
        collection,
        barcodes=barcodes,
        laboratory_name=laboratory_name,
        laboratory_id=laboratory_id,
        idempotent_replay=idempotent_replay,
        actor=actor,
    )


def _handoff_payload(
    order: BizOrder,
    collection: BizCollection | None,
    *,
    barcodes: dict[str, Any],
    laboratory_name: str,
    laboratory_id: str | None,
    idempotent_replay: bool,
    actor: str | None,
) -> dict[str, Any]:
    entry = ReceptionQueueEntry.query.filter_by(order_id=order.id).first()
    accepted_at = None
    if collection and collection.received_at:
        accepted_at = collection.received_at.isoformat()
    elif collection and collection.updated_at:
        accepted_at = collection.updated_at.isoformat()
    elif collection and collection.created_at:
        accepted_at = collection.created_at.isoformat()

    queue_reference = None
    if collection:
        queue_reference = (
            collection.accession_number
            or collection.sample_code
            or collection.barcode_value
            or collection.id
        )

    return {
        "order_code": order.order_code,
        "order_status": order.status,
        "collection": collection.to_dict() if collection else None,
        "queue_entry": entry.to_dict() if entry else None,
        "queue_reference": queue_reference,
        "laboratory": {
            "id": laboratory_id,
            "name": laboratory_name,
        },
        "accepted_at": accepted_at,
        "barcodes": {
            "order_barcode": barcodes.get("order_barcode"),
            "patient_qr": barcodes.get("patient_qr"),
            "sample_count": len(barcodes.get("sample_barcodes") or []),
        },
        "handed_off": order.status in _LAB_HANDED_OFF_STATUSES
        or _collection_is_lab_received(collection),
        "idempotent_replay": idempotent_replay,
        "actor": actor,
    }


def get_lab_handoff_status(order_ref: str) -> dict[str, Any]:
    """Refresh persistence for Milestone 4 handoff status."""
    order = BizOrder.query.filter(
        or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)
    ).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")
    collection = BizCollection.query.filter_by(order_id=order.id).first()
    barcodes = None
    try:
        if (
            payment_summary_for_order(order)["status"] == "paid"
            or order.status == ORDER_PAID
            or collection
        ):
            barcodes = generate_barcodes(order.order_code)
    except ReceptionWorkspaceError:
        barcodes = None
    handed_off = order.status in _LAB_HANDED_OFF_STATUSES or _collection_is_lab_received(
        collection
    )
    return _handoff_payload(
        order,
        collection,
        barcodes=barcodes or {},
        laboratory_name="Central Laboratory",
        laboratory_id=None,
        idempotent_replay=handed_off,
        actor=None,
    )


def _assert_order_document_eligible(order: BizOrder) -> None:
    """Milestone 3 — barcodes/requisition require a paid, non-cancelled order."""
    status = (order.status or "").lower()
    if status in {"cancelled", "canceled", "void"}:
        raise ReceptionWorkspaceError(
            f"Cannot generate documents for order in status {order.status}"
        )
    summary = payment_summary_for_order(order)
    if summary["status"] != "paid" and status != ORDER_PAID:
        raise ReceptionWorkspaceError(
            "Order must be paid before barcode, QR, or requisition generation"
        )


def generate_barcodes(order_ref: str) -> dict[str, Any]:
    """Return stable backend identifiers. Reprint returns the same codes (no new IDs)."""
    order = BizOrder.query.filter(or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")
    _assert_order_document_eligible(order)

    patient = Patient.query.get(order.patient_code)
    collection = BizCollection.query.filter_by(order_id=order.id).first()

    had_order_barcode = bool(order.barcode_value)
    order_barcode = order.barcode_value or f"BC-{order.order_code}"
    if not order.barcode_value:
        try:
            from app.business_engine.service import table_has_column

            if table_has_column("biz_orders", "barcode_value"):
                order.barcode_value = order_barcode
                db.session.flush()
        except Exception:
            # Column may be absent in some environments — still return deterministic code.
            pass

    patient_code = order.patient_code
    patient_barcode = f"BC-PAT-{patient_code}"
    patient_qr = f"dxcon:patient:{patient_code}"
    if not patient_qr.startswith("dxcon:patient:") or not patient_code:
        raise ReceptionWorkspaceError("Invalid patient QR payload")

    samples = []
    for item in order.items:
        sample_code = f"SMP-{item.test_code}-{order.order_code}"
        samples.append({
            "test_code": item.test_code,
            "test_name": item.test_name,
            "sample_type": getattr(item, "sample_type", None) or item.test_name,
            "specimen_code": sample_code,
            "barcode": f"BC-{sample_code}",
            "collection_requirement": "Follow standard collection SOP",
        })

    generated_at = datetime.utcnow().isoformat() + "Z"
    payload = {
        "order_code": order.order_code,
        "patient_code": patient_code,
        "patient_name": order.patient_name or (patient.full_name if patient else None),
        "order_barcode": order_barcode,
        "patient_barcode": patient_barcode,
        "patient_qr": patient_qr,
        "sample_barcodes": samples,
        "collection_barcode": collection.barcode_value if collection else None,
        "generated_at": generated_at,
        "reprint": had_order_barcode,
        "status": order.status,
    }
    write_reception_audit(
        action="barcode_printed" if had_order_barcode else "barcode_generated",
        object_type="order",
        object_id=order.order_code,
    )
    return payload


def render_request_form(order_ref: str) -> dict[str, Any]:
    """Return requisition HTML plus embedded identifier metadata for reprint stability."""
    order = BizOrder.query.filter(or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")
    _assert_order_document_eligible(order)
    barcodes = generate_barcodes(order_ref)
    html = biz.render_request_form_html(order)
    # Enrich with QR + specimen identifiers for printable requisition.
    sample_rows = "".join(
        f"<li>{s['test_name']} ({s['test_code']}) — specimen {s['specimen_code']} — barcode {s['barcode']}</li>"
        for s in barcodes.get("sample_barcodes") or []
    )
    enrichment = (
        f"<section><h2>Identifiers</h2>"
        f"<p>Order barcode: {barcodes['order_barcode']}</p>"
        f"<p>Patient barcode: {barcodes['patient_barcode']}</p>"
        f"<p>Patient QR: {barcodes['patient_qr']}</p>"
        f"<p>Generated at: {barcodes['generated_at']}</p>"
        f"<ul>{sample_rows or '<li>No specimen lines</li>'}</ul>"
        f"</section>"
    )
    if "</body>" in html:
        html = html.replace("</body>", enrichment + "</body>")
    else:
        html = html + enrichment
    write_reception_audit(action="request_form_printed", object_type="order", object_id=order.order_code)
    return {
        "html": html,
        "order_code": order.order_code,
        "patient_code": order.patient_code,
        "barcodes": barcodes,
        "reprint": barcodes.get("reprint", False),
        "generated_at": barcodes.get("generated_at"),
    }


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
