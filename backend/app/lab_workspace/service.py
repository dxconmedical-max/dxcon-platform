"""Laboratory operational workspace service — orchestrates business engine + LIS."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, or_

from app.business_engine import service as biz
from app.business_engine.service import BusinessEngineError
from app.business_engine.statuses import (
    ORDER_IN_TRANSIT,
    ORDER_LAB_RECEIVED,
    ORDER_PENDING_REVIEW,
    ORDER_RELEASED,
    ORDER_TESTING,
    RESULT_PENDING_REVIEW,
    RESULT_RELEASED,
    RESULT_TESTING,
)
from app.extensions.db import db
from app.lab_workspace.audit import write_lab_audit
from app.lab_workspace.flags import calculate_abnormal_flag
from app.lab_workspace.security import CONDITION_STATUSES
from app.models.biz_order import BizCollection, BizOrder, BizResult, BizResultItem
from app.models.lab_lis import LabAccessionRecord, LISImportFailedRow
from app.models.patient import Patient
from app.models.test_catalog import TestCatalog


class LabWorkspaceError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def next_accession_number() -> str:
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


def receive_sample(
    *,
    sample_code: str | None = None,
    order_code: str | None = None,
    patient_code: str | None = None,
    received_by: str,
    received_at: datetime | None = None,
    condition_status: str = "acceptable",
    note: str | None = None,
    actor: str | None = None,
) -> dict:
    if condition_status not in CONDITION_STATUSES:
        raise LabWorkspaceError(f"Invalid condition_status: {condition_status}")
    order = None
    if order_code:
        order = BizOrder.query.filter_by(order_code=order_code).first()
    if not order and sample_code:
        coll = BizCollection.query.filter_by(sample_code=sample_code).first()
        if coll:
            order = BizOrder.query.get(coll.order_id)
    if not order:
        raise LabWorkspaceError("Order not found for receive")
    if patient_code and order.patient_code != patient_code:
        raise LabWorkspaceError("Patient does not match order")

    if condition_status == "rejected":
        collection = BizCollection.query.filter_by(order_id=order.id).first()
        if collection and hasattr(collection, "condition_status"):
            collection.condition_status = "rejected"
            if hasattr(collection, "receive_note"):
                collection.receive_note = note
        write_lab_audit(action="sample_rejected", object_type="sample", object_id=sample_code or order.order_code, actor=actor)
        return {"order_code": order.order_code, "status": "rejected", "condition_status": condition_status}

    # Lab receive requires in_transit. Advance earlier milestones when the
    # specimen arrives without prior collector scan events.
    from app.business_engine.statuses import (
        ORDER_COLLECTED,
        ORDER_PAID,
        ORDER_SAMPLING,
    )

    order = BizOrder.query.filter_by(order_code=order.order_code).first()
    if order.status == ORDER_PAID:
        collection = BizCollection.query.filter_by(order_id=order.id).first()
        if not collection:
            biz.create_collection_job(
                order.order_code,
                collector_name="Lab Walk-in",
                pickup_address="Lab Reception",
                actor=actor,
            )
        order = BizOrder.query.filter_by(order_code=order.order_code).first()
    if order.status == ORDER_SAMPLING:
        biz.collect_sample(order.order_code, actor=actor)
        order = BizOrder.query.filter_by(order_code=order.order_code).first()
    if order.status == ORDER_COLLECTED:
        biz.handover_sample(order.order_code, actor=actor)
        order = BizOrder.query.filter_by(order_code=order.order_code).first()

    collection = biz.receive_sample_at_lab(order.order_code, received_by=received_by, actor=actor)
    if hasattr(collection, "condition_status"):
        collection.condition_status = condition_status
    if hasattr(collection, "receive_note"):
        collection.receive_note = note
    if received_at:
        collection.received_at = received_at
    write_lab_audit(action="sample_received", object_type="sample", object_id=collection.sample_code or order.order_code, actor=actor)
    return {
        "order_code": order.order_code,
        "sample_code": collection.sample_code,
        "status": order.status,
        "condition_status": condition_status,
        "received_by": received_by,
    }


def create_accession(
    *,
    order_code: str,
    sample_code: str | None = None,
    accessioned_by: str,
    laboratory_id: str | None = None,
    actor: str | None = None,
) -> dict:
    order = BizOrder.query.filter_by(order_code=order_code).first()
    if not order:
        raise LabWorkspaceError("Order not found")
    collection = BizCollection.query.filter_by(order_id=order.id).first()
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
    )
    db.session.add(record)
    write_lab_audit(action="accession_created", object_type="accession", object_id=acc_num, actor=actor)
    return record.to_dict()


def testing_queue(*, page: int = 1, per_page: int = 50, status: str | None = None) -> dict:
    query = BizOrder.query.filter(
        BizOrder.status.in_([ORDER_LAB_RECEIVED, ORDER_TESTING, ORDER_PENDING_REVIEW])
    )
    total = query.count()
    orders = query.order_by(BizOrder.updated_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    rows = []
    for order in orders:
        collection = BizCollection.query.filter_by(order_id=order.id).first()
        accession = LabAccessionRecord.query.filter_by(order_code=order.order_code).first()
        for item in order.items:
            result = BizResult.query.filter_by(order_id=order.id).first()
            item_status = "waiting"
            if result and result.items:
                item_status = "completed" if order.status != ORDER_TESTING else "running"
            if status and item_status != status:
                continue
            rows.append({
                "accession_number": (accession.accession_number if accession else collection.accession_number if collection else None),
                "sample_code": collection.sample_code if collection else None,
                "patient": order.patient_name,
                "patient_code": order.patient_code,
                "order_code": order.order_code,
                "test_code": item.test_code,
                "test_name": item.test_name,
                "department": item.test_name,
                "analyzer": "—",
                "priority": "routine",
                "status": item_status,
            })
    return {"data": rows, "pagination": {"page": page, "per_page": per_page, "total": total}}


def enter_result_manual(
    order_code: str,
    *,
    test_code: str,
    result_value: str,
    unit: str | None = None,
    reference_range: str | None = None,
    abnormal_flag: str | None = None,
    instrument: str | None = None,
    technician: str | None = None,
    result_time: datetime | None = None,
    note: str | None = None,
    revision_mode: bool = False,
    actor: str | None = None,
) -> dict:
    catalog = TestCatalog.query.filter_by(code=test_code).first()
    order = BizOrder.query.filter_by(order_code=order_code).first()
    if not order:
        raise LabWorkspaceError("Order not found")
    if not catalog:
        # Fall back to an order line item so barcode/test codes from the order work.
        from app.models.biz_order import BizOrderItem

        line = BizOrderItem.query.filter_by(order_id=order.id, test_code=test_code).first()
        if not line and order.items:
            line = order.items[0]
            test_code = line.test_code
        if not line:
            raise LabWorkspaceError("Test not found in Master Data")
        catalog_name = line.test_name
        catalog_unit = unit or ""
    else:
        catalog_name = catalog.name
        catalog_unit = unit or ""
    if order.status == ORDER_RELEASED:
        raise LabWorkspaceError("Order already released")

    ref = reference_range or ""
    flag, warnings = calculate_abnormal_flag(result_value, reference_range=ref, manual_flag=abnormal_flag)

    if not revision_mode:
        result_existing = BizResult.query.filter_by(order_id=order.id).first()
        if result_existing:
            dup = BizResultItem.query.filter_by(result_id=result_existing.id, test_code=test_code).first()
            if dup:
                raise LabWorkspaceError("Duplicate result; enable revision_mode to overwrite")

    items = [{
        "test_code": test_code,
        "test_name": catalog_name,
        "result_value": result_value,
        "unit": catalog_unit,
        "reference_range": ref,
        "flag": flag.upper(),
    }]
    result = biz.enter_results(order_code, items, actor=actor)
    item = BizResultItem.query.filter_by(result_id=result.id, test_code=test_code).first()
    if item:
        if hasattr(item, "instrument") and instrument:
            item.instrument = instrument
        if hasattr(item, "technician"):
            item.technician = technician or actor
        if hasattr(item, "result_time"):
            item.result_time = result_time or _utcnow()
        if hasattr(item, "entry_note"):
            item.entry_note = note
    if hasattr(result, "workflow_status"):
        result.workflow_status = "entered"
    write_lab_audit(action="result_entered", object_type="result", object_id=result.result_code, actor=actor)
    return {"result": result.to_dict(), "flag": flag, "warnings": warnings}


def mark_qc_passed(order_code: str, *, note: str | None = None, actor: str | None = None) -> dict:
    result = biz.complete_qc(order_code, actor=actor)
    if hasattr(result, "workflow_status"):
        result.workflow_status = "qc_passed"
    write_lab_audit(action="qc_passed", object_type="result", object_id=result.result_code, actor=actor)
    return result.to_dict()


def mark_qc_failed(order_code: str, *, note: str | None = None, actor: str | None = None) -> dict:
    order = BizOrder.query.filter_by(order_code=order_code).first()
    if not order:
        raise LabWorkspaceError("Order not found")
    result = BizResult.query.filter_by(order_id=order.id).first()
    if not result:
        raise LabWorkspaceError("Result not found")
    if hasattr(result, "workflow_status"):
        result.workflow_status = "qc_pending"
    write_lab_audit(action="qc_failed", object_type="result", object_id=result.result_code, actor=actor)
    return {"result_code": result.result_code, "status": "qc_failed", "note": note}


def validate_result(order_code: str, *, actor: str | None = None) -> dict:
    order = BizOrder.query.filter_by(order_code=order_code).first()
    if not order:
        raise LabWorkspaceError("Order not found")
    result = BizResult.query.filter_by(order_id=order.id).first()
    if not result:
        raise LabWorkspaceError("Result not found")
    if hasattr(result, "workflow_status"):
        result.workflow_status = "pending_review"
    result.status = RESULT_PENDING_REVIEW
    order.status = ORDER_PENDING_REVIEW
    write_lab_audit(action="result_validated", object_type="result", object_id=result.result_code, actor=actor)
    write_lab_audit(action="sent_to_doctor_review", object_type="order", object_id=order_code, actor=actor)
    return {"order_code": order_code, "result_code": result.result_code, "status": "pending_review"}


def reject_result(order_code: str, *, reason: str | None = None, actor: str | None = None) -> dict:
    order = BizOrder.query.filter_by(order_code=order_code).first()
    result = BizResult.query.filter_by(order_id=order.id).first() if order else None
    if result and hasattr(result, "workflow_status"):
        result.workflow_status = "validation_required"
    write_lab_audit(action="result_rejected", object_type="result", object_id=result.result_code if result else order_code, actor=actor)
    return {"order_code": order_code, "reason": reason, "status": "validation_required"}


def workspace_dashboard() -> dict[str, Any]:
    incoming = biz.list_lab_incoming(limit=50)
    received = BizOrder.query.filter_by(status=ORDER_LAB_RECEIVED).count()
    testing = BizOrder.query.filter_by(status=ORDER_TESTING).count()
    pending_validation = BizResult.query.filter(
        or_(BizResult.workflow_status == "validation_required", BizResult.result_source == "imported")
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

    accession_queue = [r.to_dict() for r in LabAccessionRecord.query.order_by(LabAccessionRecord.created_at.desc()).limit(20).all()]
    qc_queue = [
        r.to_dict()
        for r in BizResult.query.filter(BizResult.status == RESULT_TESTING).limit(20).all()
    ]

    return {
        "widgets": [
            "incoming_samples", "received_samples", "accession_queue", "testing_queue",
            "qc_queue", "pending_validation", "pending_doctor_review", "released_today",
            "failed_lis_imports", "critical_abnormal_results",
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
        },
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
        "imported_never_auto_release": True,
        "import_requires_validation": True,
    }
