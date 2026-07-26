"""Laboratory operational workspace — specimen receive through medical validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, or_

from app.business_engine import service as biz
from app.business_engine.service import BusinessEngineError
from app.business_engine.statuses import (
    ORDER_APPROVED,
    ORDER_IN_TRANSIT,
    ORDER_LAB_RECEIVED,
    ORDER_PENDING_REVIEW,
    ORDER_RELEASED,
    ORDER_TESTING,
    RESULT_APPROVED,
    RESULT_PENDING_REVIEW,
    RESULT_RELEASED,
    RESULT_TESTING,
)
from app.extensions.db import db
from app.lab_workspace.audit import write_lab_audit
from app.lab_workspace.flags import calculate_abnormal_flag
from app.lab_workspace.security import (
    CONDITION_STATUSES,
    LAB_STATUS_EXCEPTIONS,
    LAB_STATUS_FLOW,
    LOCKED_ORDER_STATUSES,
    LOCKED_RESULT_WORKFLOW,
    PROCESSING_STATUSES,
    REJECTION_REASONS,
    RESULT_WORKFLOW_STATUSES,
)
from app.models.biz_order import BizCollection, BizOrder, BizResult, BizResultItem, BizWorkflowAudit
from app.models.lab_lis import LabAccessionRecord, LISImportFailedRow
from app.models.test_catalog import TestCatalog


class LabWorkspaceError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def status_contract() -> dict[str, Any]:
    return {
        "order_flow": list(LAB_STATUS_FLOW),
        "exceptions": list(LAB_STATUS_EXCEPTIONS),
        "processing": list(PROCESSING_STATUSES),
        "result_workflow": list(RESULT_WORKFLOW_STATUSES),
        "condition_statuses": list(CONDITION_STATUSES),
        "rejection_reasons": list(REJECTION_REASONS),
        "accession_id_format": "ACC-YYYYMMDD-000001",
    }


def next_accession_number() -> str:
    """Synthetic accession ID: ACC-YYYYMMDD-000001."""
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"ACC-{today}-"
    last = (
        LabAccessionRecord.query.filter(LabAccessionRecord.accession_number.like(f"{prefix}%"))
        .order_by(LabAccessionRecord.accession_number.desc())
        .first()
    )
    if last:
        try:
            seq = int(last.accession_number.split("-")[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:06d}"


def _get_order(order_code: str | None = None, sample_code: str | None = None) -> BizOrder:
    order = None
    if order_code:
        order = BizOrder.query.filter_by(order_code=order_code).first()
    if not order and sample_code:
        coll = BizCollection.query.filter_by(sample_code=sample_code).first()
        if coll:
            order = BizOrder.query.get(coll.order_id)
    if not order:
        raise LabWorkspaceError("Order not found")
    return order


def _collection_for(order: BizOrder) -> BizCollection | None:
    return BizCollection.query.filter_by(order_id=order.id).first()


def _accession_for(order: BizOrder) -> LabAccessionRecord | None:
    return LabAccessionRecord.query.filter_by(order_code=order.order_code).first()


def _assert_editable(order: BizOrder, result: BizResult | None = None) -> None:
    if order.status in LOCKED_ORDER_STATUSES or order.status == ORDER_RELEASED:
        raise LabWorkspaceError("Order results are finalized and immutable")
    result = result or BizResult.query.filter_by(order_id=order.id).first()
    if result and (result.workflow_status or "") in LOCKED_RESULT_WORKFLOW:
        raise LabWorkspaceError(
            "Results locked after technical/medical validation; reject to reopen or use authorized revision"
        )
    if result and result.status in {RESULT_APPROVED, RESULT_RELEASED}:
        raise LabWorkspaceError("Finalized results are immutable")


def verify_identifiers(
    *,
    order_code: str | None = None,
    sample_code: str | None = None,
    barcode_value: str | None = None,
    patient_code: str | None = None,
    actor: str | None = None,
) -> dict:
    order = _get_order(order_code=order_code, sample_code=sample_code)
    collection = _collection_for(order)
    mismatches: list[str] = []

    if sample_code and collection and collection.sample_code and sample_code != collection.sample_code:
        mismatches.append("sample_code")
    if barcode_value and collection and collection.barcode_value and barcode_value != collection.barcode_value:
        mismatches.append("barcode_value")
    if patient_code and patient_code != order.patient_code:
        mismatches.append("patient_code")
    if not collection:
        mismatches.append("collection_missing")

    ok = len(mismatches) == 0
    accession = _accession_for(order)
    if accession and ok:
        accession.identifiers_verified = True
        accession.verified_at = _utcnow()

    write_lab_audit(
        action="identifiers_verified" if ok else "identifiers_mismatch",
        object_type="order",
        object_id=order.order_code,
        actor=actor,
    )
    return {
        "ok": ok,
        "order_code": order.order_code,
        "patient_code": order.patient_code,
        "sample_code": collection.sample_code if collection else None,
        "barcode_value": collection.barcode_value if collection else None,
        "mismatches": mismatches,
        "condition_status": collection.condition_status if collection else None,
    }


def receive_sample(
    *,
    sample_code: str | None = None,
    order_code: str | None = None,
    patient_code: str | None = None,
    barcode_value: str | None = None,
    received_by: str,
    received_at: datetime | None = None,
    condition_status: str = "acceptable",
    rejection_reason: str | None = None,
    note: str | None = None,
    actor: str | None = None,
) -> dict:
    if condition_status not in CONDITION_STATUSES:
        raise LabWorkspaceError(f"Invalid condition_status: {condition_status}")
    order = _get_order(order_code=order_code, sample_code=sample_code)
    if patient_code and order.patient_code != patient_code:
        raise LabWorkspaceError("Patient does not match order")

    collection = _collection_for(order)
    if barcode_value and collection and collection.barcode_value and barcode_value != collection.barcode_value:
        raise LabWorkspaceError("Barcode does not match collection")
    if sample_code and collection and collection.sample_code and sample_code != collection.sample_code:
        raise LabWorkspaceError("Sample code does not match collection")

    rejected = condition_status == "rejected" or (rejection_reason and rejection_reason in REJECTION_REASONS)
    if rejected:
        reason = rejection_reason or condition_status
        if reason not in REJECTION_REASONS and reason != "rejected":
            raise LabWorkspaceError(f"Invalid rejection_reason: {reason}")
        if reason == "rejected":
            reason = "other"
        if not note and reason == "other":
            raise LabWorkspaceError("note is required when rejection_reason is other")
        if collection:
            collection.condition_status = "rejected"
            collection.receive_note = note or reason
            if received_by:
                collection.received_by = received_by
            collection.received_at = received_at or _utcnow()
        write_lab_audit(
            action="sample_rejected",
            object_type="sample",
            object_id=sample_code or order.order_code,
            actor=actor,
        )
        return {
            "order_code": order.order_code,
            "sample_code": collection.sample_code if collection else sample_code,
            "status": "rejected",
            "condition_status": "rejected",
            "rejection_reason": reason,
            "note": note,
        }

    if order.status == ORDER_LAB_RECEIVED:
        # Idempotent refresh
        if collection:
            collection.condition_status = condition_status
            if note:
                collection.receive_note = note
        return {
            "order_code": order.order_code,
            "sample_code": collection.sample_code if collection else sample_code,
            "status": order.status,
            "condition_status": condition_status,
            "received_by": collection.received_by if collection else received_by,
            "idempotent": True,
        }

    collection = biz.receive_sample_at_lab(order.order_code, received_by=received_by, actor=actor)
    collection.condition_status = condition_status
    collection.receive_note = note
    if received_at:
        collection.received_at = received_at
    write_lab_audit(
        action="sample_received",
        object_type="sample",
        object_id=collection.sample_code or order.order_code,
        actor=actor,
    )
    return {
        "order_code": order.order_code,
        "sample_code": collection.sample_code,
        "status": order.status,
        "condition_status": condition_status,
        "received_by": received_by,
        "received_at": collection.received_at.isoformat() if collection.received_at else None,
        "accession_number": collection.accession_number,
    }


def create_accession(
    *,
    order_code: str,
    sample_code: str | None = None,
    accessioned_by: str,
    laboratory_id: str | None = None,
    actor: str | None = None,
) -> dict:
    order = _get_order(order_code=order_code)
    if order.status not in {ORDER_LAB_RECEIVED, ORDER_TESTING}:
        raise LabWorkspaceError(f"Accession requires lab_received status, got {order.status}")
    collection = _collection_for(order)
    if collection and collection.condition_status == "rejected":
        raise LabWorkspaceError("Cannot accession a rejected specimen")

    existing = _accession_for(order)
    if existing:
        return existing.to_dict()

    acc_num = next_accession_number()
    if collection:
        collection.accession_number = acc_num
        if sample_code:
            collection.sample_code = sample_code

    record = LabAccessionRecord(
        accession_number=acc_num,
        order_id=order.id,
        order_code=order.order_code,
        sample_code=sample_code or (collection.sample_code if collection else None),
        patient_code=order.patient_code,
        accessioned_by=accessioned_by,
        accessioned_at=_utcnow(),
        laboratory_id=laboratory_id,
        processing_status="accessioned",
        identifiers_verified=True,
        verified_at=_utcnow(),
    )
    db.session.add(record)
    write_lab_audit(action="accession_created", object_type="accession", object_id=acc_num, actor=actor)
    return record.to_dict()


def assign_processing(
    *,
    order_code: str,
    bench_id: str | None = None,
    instrument_id: str | None = None,
    technician: str | None = None,
    actor: str | None = None,
) -> dict:
    order = _get_order(order_code=order_code)
    accession = _accession_for(order)
    if not accession:
        raise LabWorkspaceError("Accession required before assignment")
    if accession.processing_status == "rejected":
        raise LabWorkspaceError("Cannot assign a rejected accession")

    if bench_id is not None:
        accession.bench_id = bench_id
    if instrument_id is not None:
        accession.instrument_id = instrument_id
    if technician is not None:
        accession.technician = technician
    elif actor and not accession.technician:
        accession.technician = actor
    accession.processing_status = "assigned"
    write_lab_audit(action="processing_assigned", object_type="accession", object_id=accession.accession_number, actor=actor)
    return accession.to_dict()


def start_processing(*, order_code: str, actor: str | None = None) -> dict:
    order = _get_order(order_code=order_code)
    accession = _accession_for(order)
    if not accession:
        raise LabWorkspaceError("Accession required before processing")
    accession.processing_status = "processing"
    accession.processing_started_at = accession.processing_started_at or _utcnow()
    write_lab_audit(action="processing_started", object_type="accession", object_id=accession.accession_number, actor=actor)
    return accession.to_dict()


def complete_processing(*, order_code: str, actor: str | None = None) -> dict:
    order = _get_order(order_code=order_code)
    accession = _accession_for(order)
    if not accession:
        raise LabWorkspaceError("Accession required")
    if not accession.processing_started_at:
        accession.processing_started_at = _utcnow()
    accession.processing_completed_at = _utcnow()
    if accession.processing_status == "processing":
        accession.processing_status = "results_entered"
    write_lab_audit(
        action="processing_completed",
        object_type="accession",
        object_id=accession.accession_number,
        actor=actor,
    )
    return accession.to_dict()


def testing_queue(*, page: int = 1, per_page: int = 50, status: str | None = None) -> dict:
    query = BizOrder.query.filter(
        BizOrder.status.in_([ORDER_LAB_RECEIVED, ORDER_TESTING, ORDER_PENDING_REVIEW, ORDER_APPROVED])
    )
    total = query.count()
    orders = query.order_by(BizOrder.updated_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    rows = []
    for order in orders:
        collection = _collection_for(order)
        accession = _accession_for(order)
        result = BizResult.query.filter_by(order_id=order.id).first()
        for item in order.items:
            item_status = "waiting"
            if result and result.items:
                item_status = "completed" if order.status != ORDER_TESTING else "running"
            if status and item_status != status:
                continue
            rows.append({
                "accession_number": (
                    accession.accession_number
                    if accession
                    else (collection.accession_number if collection else None)
                ),
                "sample_code": collection.sample_code if collection else None,
                "patient": order.patient_name,
                "patient_code": order.patient_code,
                "order_code": order.order_code,
                "order_status": order.status,
                "processing_status": accession.processing_status if accession else None,
                "bench_id": accession.bench_id if accession else None,
                "instrument_id": accession.instrument_id if accession else None,
                "technician": accession.technician if accession else None,
                "test_code": item.test_code,
                "test_name": item.test_name,
                "department": item.test_name,
                "analyzer": (accession.instrument_id if accession and accession.instrument_id else "—"),
                "priority": "routine",
                "status": item_status,
                "workflow_status": result.workflow_status if result else None,
            })
    return {"data": rows, "pagination": {"page": page, "per_page": per_page, "total": total}}


def get_order_workspace(order_code: str) -> dict:
    order = _get_order(order_code=order_code)
    collection = _collection_for(order)
    accession = _accession_for(order)
    result = BizResult.query.filter_by(order_id=order.id).first()
    audits = (
        BizWorkflowAudit.query.filter(
            or_(
                BizWorkflowAudit.entity_id == order.order_code,
                BizWorkflowAudit.entity_id == (result.result_code if result else ""),
                BizWorkflowAudit.entity_id == (accession.accession_number if accession else ""),
            )
        )
        .order_by(BizWorkflowAudit.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "order": order.to_dict(),
        "collection": collection.to_dict() if collection else None,
        "accession": accession.to_dict() if accession else None,
        "result": result.to_dict() if result else None,
        "audits": [a.to_dict() for a in audits],
        "status_contract": status_contract(),
        "locked": bool(
            order.status in LOCKED_ORDER_STATUSES
            or (result and (result.workflow_status or "") in LOCKED_RESULT_WORKFLOW)
        ),
    }


def enter_result_manual(
    order_code: str,
    *,
    test_code: str,
    result_value: str,
    unit: str | None = None,
    reference_range: str | None = None,
    abnormal_flag: str | None = None,
    critical_low: float | None = None,
    critical_high: float | None = None,
    instrument: str | None = None,
    technician: str | None = None,
    result_time: datetime | None = None,
    note: str | None = None,
    revision_mode: bool = False,
    actor: str | None = None,
) -> dict:
    if not str(result_value or "").strip():
        raise LabWorkspaceError("result_value is required")

    catalog = TestCatalog.query.filter_by(code=test_code).first()
    if not catalog:
        raise LabWorkspaceError("Test not found in Master Data")
    order = _get_order(order_code=order_code)
    result_existing = BizResult.query.filter_by(order_id=order.id).first()
    _assert_editable(order, result_existing)

    if not revision_mode and result_existing:
        dup = BizResultItem.query.filter_by(result_id=result_existing.id, test_code=test_code).first()
        if dup:
            raise LabWorkspaceError("Duplicate result; enable revision_mode to overwrite")

    ref = reference_range or ""
    flag, warnings = calculate_abnormal_flag(
        result_value,
        reference_range=ref,
        manual_flag=abnormal_flag,
        critical_low=critical_low,
        critical_high=critical_high,
    )
    if not unit:
        warnings.append("Unit not provided")

    accession = _accession_for(order)
    items = [{
        "test_code": test_code,
        "test_name": catalog.name,
        "result_value": result_value,
        "unit": unit or "",
        "reference_range": ref,
        "flag": flag.upper(),
    }]
    result = biz.enter_results(order_code, items, actor=actor)
    item = BizResultItem.query.filter_by(result_id=result.id, test_code=test_code).first()
    if item:
        item.instrument = instrument or (accession.instrument_id if accession else None)
        item.technician = technician or (accession.technician if accession else None) or actor
        item.result_time = result_time or _utcnow()
        item.entry_note = note
    result.workflow_status = "entered"
    result.result_source = "manual"
    if accession:
        accession.processing_status = "results_entered"
        if not accession.processing_started_at:
            accession.processing_started_at = _utcnow()
    write_lab_audit(action="result_entered", object_type="result", object_id=result.result_code, actor=actor)
    return {
        "result": result.to_dict(),
        "flag": flag,
        "warnings": warnings,
        "critical": flag in {"critical_low", "critical_high"},
    }


def ingest_analyzer_result(
    order_code: str,
    *,
    test_code: str,
    result_value: str,
    unit: str | None = None,
    reference_range: str | None = None,
    instrument: str | None = None,
    technician: str | None = None,
    critical_low: float | None = None,
    critical_high: float | None = None,
    actor: str | None = None,
) -> dict:
    """Analyzer / LIS ingestion hook — never auto-releases; requires validation."""
    data = enter_result_manual(
        order_code,
        test_code=test_code,
        result_value=result_value,
        unit=unit,
        reference_range=reference_range,
        instrument=instrument,
        technician=technician,
        critical_low=critical_low,
        critical_high=critical_high,
        revision_mode=True,
        actor=actor,
    )
    order = _get_order(order_code=order_code)
    result = BizResult.query.filter_by(order_id=order.id).first()
    if result:
        result.result_source = "analyzer"
        result.workflow_status = "analyzer"
    write_lab_audit(action="analyzer_result_ingested", object_type="result", object_id=order_code, actor=actor)
    data["result_source"] = "analyzer"
    data["requires_validation"] = True
    return data


def mark_qc_passed(order_code: str, *, note: str | None = None, actor: str | None = None) -> dict:
    order = _get_order(order_code=order_code)
    result = BizResult.query.filter_by(order_id=order.id).first()
    if not result or not result.items:
        raise LabWorkspaceError("No result items to QC")
    _assert_editable(order, result)
    if order.status != ORDER_TESTING:
        raise LabWorkspaceError(f"QC requires testing status, got {order.status}")
    result.workflow_status = "qc_passed"
    write_lab_audit(action="qc_passed", object_type="result", object_id=result.result_code, actor=actor)
    return {**result.to_dict(), "note": note, "qc_status": "passed"}


def mark_qc_failed(order_code: str, *, note: str | None = None, actor: str | None = None) -> dict:
    order = _get_order(order_code=order_code)
    result = BizResult.query.filter_by(order_id=order.id).first()
    if not result:
        raise LabWorkspaceError("Result not found")
    result.workflow_status = "qc_pending"
    write_lab_audit(action="qc_failed", object_type="result", object_id=result.result_code, actor=actor)
    return {"result_code": result.result_code, "status": "qc_failed", "note": note}


def validate_result(order_code: str, *, actor: str | None = None) -> dict:
    """Technical validation — locks results and sends to medical review."""
    order = _get_order(order_code=order_code)
    result = BizResult.query.filter_by(order_id=order.id).first()
    if not result or not result.items:
        raise LabWorkspaceError("Result not found")
    if (result.workflow_status or "") in {"approved", "released"}:
        raise LabWorkspaceError("Already medically finalized")
    if (result.workflow_status or "") not in {
        "entered",
        "qc_passed",
        "qc_pending",
        "validation_required",
        "analyzer",
        "imported",
        "pending_review",
    }:
        raise LabWorkspaceError(f"Cannot technically validate from workflow_status={result.workflow_status}")

    if order.status == ORDER_TESTING:
        try:
            biz.complete_qc(order_code, actor=actor)
            order = _get_order(order_code=order_code)
            result = BizResult.query.filter_by(order_id=order.id).first()
        except BusinessEngineError:
            result.status = RESULT_PENDING_REVIEW
            order.status = ORDER_PENDING_REVIEW
    else:
        result.status = RESULT_PENDING_REVIEW
        if order.status == ORDER_LAB_RECEIVED:
            order.status = ORDER_PENDING_REVIEW

    result.workflow_status = "pending_review"
    accession = _accession_for(order)
    if accession:
        accession.processing_status = "tech_validated"
        accession.processing_completed_at = accession.processing_completed_at or _utcnow()

    write_lab_audit(action="technical_validation", object_type="result", object_id=result.result_code, actor=actor)
    write_lab_audit(action="sent_to_doctor_review", object_type="order", object_id=order_code, actor=actor)
    return {
        "order_code": order_code,
        "result_code": result.result_code,
        "status": "pending_review",
        "workflow_status": result.workflow_status,
        "locked": True,
    }


def reject_result(order_code: str, *, reason: str | None = None, actor: str | None = None) -> dict:
    order = _get_order(order_code=order_code)
    if order.status in {ORDER_APPROVED, ORDER_RELEASED}:
        raise LabWorkspaceError("Cannot reject medically finalized results")
    result = BizResult.query.filter_by(order_id=order.id).first()
    if not result:
        raise LabWorkspaceError("Result not found")
    result.workflow_status = "validation_required"
    if order.status == ORDER_PENDING_REVIEW:
        order.status = ORDER_TESTING
        result.status = RESULT_TESTING
    accession = _accession_for(order)
    if accession:
        accession.processing_status = "results_entered"
    write_lab_audit(action="result_rejected", object_type="result", object_id=result.result_code, actor=actor)
    return {"order_code": order_code, "reason": reason, "status": "validation_required", "locked": False}


def medical_validate(
    order_code: str,
    *,
    doctor_note: str | None = None,
    actor: str | None = None,
) -> dict:
    """Medical / doctor validation — final clinical sign-off (immutable thereafter)."""
    order = _get_order(order_code=order_code)
    result = BizResult.query.filter_by(order_id=order.id).first()
    if not result:
        raise LabWorkspaceError("Result not found")
    if order.status != ORDER_PENDING_REVIEW and (result.workflow_status or "") != "pending_review":
        raise LabWorkspaceError("Medical validation requires prior technical validation")
    if order.status in {ORDER_APPROVED, ORDER_RELEASED}:
        return {
            "order_code": order_code,
            "result_code": result.result_code,
            "status": order.status,
            "workflow_status": result.workflow_status,
            "idempotent": True,
            "locked": True,
        }

    approved = biz.approve_result(order_code, doctor_note=doctor_note, actor=actor)
    approved.workflow_status = "approved"
    accession = _accession_for(order)
    if accession:
        accession.processing_status = "medically_validated"
        accession.processing_completed_at = accession.processing_completed_at or _utcnow()
    write_lab_audit(action="medical_validation", object_type="result", object_id=approved.result_code, actor=actor)
    return {
        "order_code": order_code,
        "result_code": approved.result_code,
        "status": ORDER_APPROVED,
        "workflow_status": "approved",
        "locked": True,
        "approved_by": approved.approved_by,
        "approved_at": approved.approved_at.isoformat() if approved.approved_at else None,
    }


def workspace_dashboard() -> dict[str, Any]:
    incoming = biz.list_lab_incoming(limit=50)
    received = BizOrder.query.filter_by(status=ORDER_LAB_RECEIVED).count()
    testing = BizOrder.query.filter_by(status=ORDER_TESTING).count()
    pending_validation = BizResult.query.filter(
        or_(
            BizResult.workflow_status.in_(["validation_required", "entered", "qc_passed", "analyzer", "imported"]),
            BizResult.result_source.in_(["imported", "analyzer"]),
        )
    ).count()
    pending_review = BizResult.query.filter_by(status=RESULT_PENDING_REVIEW).count()
    today = datetime.utcnow().date()
    released_today = BizResult.query.filter(
        BizResult.status == RESULT_RELEASED,
        func.date(BizResult.released_at) == today,
    ).count()
    failed_imports = LISImportFailedRow.query.filter_by(status="failed").count()
    abnormal = BizResultItem.query.filter(
        BizResultItem.flag.in_(["HIGH", "LOW", "CRITICAL_LOW", "CRITICAL_HIGH", "ABNORMAL"])
    ).count()
    rejected = BizCollection.query.filter_by(condition_status="rejected").count()

    accession_queue = [
        r.to_dict()
        for r in LabAccessionRecord.query.order_by(LabAccessionRecord.created_at.desc()).limit(20).all()
    ]
    qc_queue = [r.to_dict() for r in BizResult.query.filter(BizResult.status == RESULT_TESTING).limit(20).all()]

    return {
        "widgets": [
            "incoming_samples",
            "received_samples",
            "accession_queue",
            "testing_queue",
            "qc_queue",
            "pending_validation",
            "pending_doctor_review",
            "released_today",
            "failed_lis_imports",
            "critical_abnormal_results",
        ],
        "kpis": {
            "incoming": len(incoming),
            "received": received,
            "testing": testing,
            "pending_validation": pending_validation,
            "pending_review": pending_review,
            "released_today": released_today,
            "failed_imports": failed_imports,
            "abnormal_results": abnormal,
            "rejected": rejected,
        },
        "status_contract": status_contract(),
        "incoming_samples": incoming,
        "accession_queue": accession_queue,
        "testing_queue": testing_queue(per_page=20)["data"],
        "qc_queue": qc_queue,
        "pending_review": biz.list_pending_doctor_reviews(limit=20),
        "failed_imports": failed_imports,
    }


def lab_workspace_report() -> dict:
    dash = workspace_dashboard()
    return {"report": "LAB_WORKSPACE_REPORT", **dash["kpis"], "widgets": len(dash["widgets"])}


def lab_security_report() -> dict:
    from app.core.permissions import role_has_permission

    return {
        "report": "LAB_SECURITY_REPORT",
        "lab_technician_can_receive": role_has_permission("LAB", "lab.receive"),
        "lab_technician_cannot_release": not role_has_permission("LAB", "report.release"),
        "lab_cannot_medical_validate": not role_has_permission("LAB", "report.approve"),
        "doctor_can_medical_validate": role_has_permission("DOCTOR", "report.approve"),
        "imported_never_auto_release": True,
        "import_requires_validation": True,
        "finalized_immutable": True,
    }
