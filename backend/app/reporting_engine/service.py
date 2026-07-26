"""Reporting engine service — doctor review, release, patient visibility."""

from __future__ import annotations

from datetime import datetime
import json
from typing import Any

from sqlalchemy import or_

from app.business_engine import service as biz
from app.business_engine.service import BusinessEngineError
from app.business_engine.statuses import (
    ORDER_APPROVED,
    ORDER_RELEASED,
    RESULT_APPROVED,
    RESULT_PENDING_REVIEW,
    RESULT_RELEASED,
)
from app.extensions.db import db
from app.models.audit_log import AuditLog
from app.models.biz_order import BizCollection, BizOrder, BizResult, BizWorkflowAudit
from app.models.clinical_report import ClinicalReport, CriticalResultAlert, ReportDigitalSignature, ReportNotificationEvent
from app.models.lab_lis import LabAccessionRecord
from app.reporting_engine.audit import write_report_audit
from app.reporting_engine.pdf_service import (
    REPORT_PDF_TEMPLATE_ID,
    REPORT_PDF_TEMPLATE_VERSION,
    ReportPdfError,
    read_pdf_bytes,
    resolve_pdf_path,
    write_report_pdf,
)
from app.reporting_engine.report_generation_service import (
    build_report_payload,
    build_verify_url,
    generate_qr_payload,
    generate_report_code,
    generate_report_hash,
    prepare_pdf_payload,
    render_html_report,
)


class ReportingEngineError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def _count_flags(result: BizResult) -> tuple[int, int]:
    abnormal = critical = 0
    for item in result.items:
        flag = (item.flag or "").upper()
        if flag and flag not in ("NORMAL",):
            abnormal += 1
        if "CRITICAL" in flag:
            critical += 1
    return abnormal, critical


def ensure_clinical_report(order: BizOrder, *, result: BizResult | None = None) -> ClinicalReport:
    existing = ClinicalReport.query.filter_by(order_id=order.id).order_by(ClinicalReport.report_version.desc()).first()
    if existing and existing.report_status not in ("cancelled",):
        return existing
    result = result or BizResult.query.filter_by(order_id=order.id).first()
    collection = BizCollection.query.filter_by(order_id=order.id).first()
    accession = LabAccessionRecord.query.filter_by(order_code=order.order_code).first()
    status = "pending_review"
    if result and result.status == RESULT_APPROVED:
        status = "approved"
    elif result and result.status == RESULT_RELEASED:
        status = "released"
    elif result and getattr(result, "workflow_status", None) == "in_review":
        status = "in_review"
    report = ClinicalReport(
        report_code=generate_report_code(),
        order_id=order.id,
        order_code=order.order_code,
        patient_id=order.patient_code,
        result_id=result.id if result else None,
        accession_id=accession.id if accession else None,
        accession_number=(accession.accession_number if accession else (collection.accession_number if collection else None)),
        report_status=status,
    )
    db.session.add(report)
    db.session.flush()
    _scan_critical_results(order, result, report)
    write_report_audit(action="report_generated", object_type="clinical_report", object_id=report.report_code)
    return report


def _scan_critical_results(order: BizOrder, result: BizResult | None, report: ClinicalReport) -> None:
    if not result:
        return
    for item in result.items:
        flag = (item.flag or "").upper()
        if "CRITICAL" in flag or flag in ("HIGH", "LOW"):
            if "CRITICAL" not in flag:
                continue
            existing = CriticalResultAlert.query.filter_by(order_id=order.id, critical_type=flag, status="new").first()
            if existing:
                continue
            db.session.add(
                CriticalResultAlert(
                    patient_id=order.patient_code,
                    order_id=order.id,
                    order_code=order.order_code,
                    result_id=result.id,
                    report_id=report.id,
                    critical_type=flag,
                    status="new",
                )
            )


def review_queue(
    *,
    patient: str | None = None,
    order_code: str | None = None,
    critical_only: bool = False,
    status: str | None = None,
    page: int = 1,
    per_page: int = 25,
) -> dict[str, Any]:
    query = ClinicalReport.query.filter(
        ClinicalReport.report_status.in_(("pending_review", "in_review", "approved", "rejected"))
    )
    if not ClinicalReport.query.filter(ClinicalReport.report_status.in_(("pending_review", "in_review"))).count():
        for result in BizResult.query.filter_by(status=RESULT_PENDING_REVIEW).all():
            order = BizOrder.query.get(result.order_id)
            if order:
                ensure_clinical_report(order, result=result)
        db.session.flush()

    if status:
        query = ClinicalReport.query.filter_by(report_status=status)
    if order_code:
        query = query.filter(ClinicalReport.order_code.ilike(f"%{order_code}%"))
    if patient:
        query = query.filter(
            or_(ClinicalReport.patient_id.ilike(f"%{patient}%"), ClinicalReport.order_code.ilike(f"%{patient}%"))
        )
    total = query.count()
    reports = query.order_by(ClinicalReport.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    rows = []
    for report in reports:
        order = BizOrder.query.get(report.order_id)
        result = BizResult.query.filter_by(order_id=report.order_id).first()
        abnormal, critical = _count_flags(result) if result else (0, 0)
        if critical_only and critical == 0:
            continue
        rows.append({
            **report.to_dict(),
            "patient_name": order.patient_name if order else report.patient_id,
            "test_count": len(result.items) if result else 0,
            "abnormal_count": abnormal,
            "critical_count": critical,
            "priority": "critical" if critical else "routine",
            "lab_validated_at": result.created_at.isoformat() if result and result.created_at else None,
        })
    return {"data": rows, "pagination": {"page": page, "per_page": per_page, "total": total}}


def review_detail(order_ref: str) -> dict[str, Any]:
    order = BizOrder.query.filter(or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)).first()
    if not order:
        raise ReportingEngineError("Order not found")
    report = ClinicalReport.query.filter_by(order_id=order.id).order_by(ClinicalReport.report_version.desc()).first()
    if not report:
        report = ensure_clinical_report(order)
    payload = build_report_payload(order.id)
    result = BizResult.query.filter_by(order_id=order.id).first()
    timeline = audit_timeline(report.report_code)
    return {
        "report": report.to_dict(),
        "patient_summary": payload["patient"],
        "order_summary": payload["order"],
        "collection_summary": payload.get("collection"),
        "accession_summary": payload.get("accession"),
        "laboratory_summary": payload.get("laboratory"),
        "result_items": payload.get("items", []),
        "abnormal_count": payload.get("abnormal_count", 0),
        "critical_count": payload.get("critical_count", 0),
        "historical_comparison": {"placeholder": True},
        "lab_note": report.lab_note,
        "doctor_note": report.doctor_note or (result.doctor_note if result else None),
        "ai_interpretation": {"placeholder": True, "advisory": "Human review required"},
        "report_preview_html": report.html_content or render_html_report(
            payload,
            report_code=report.report_code,
            doctor_note=report.doctor_note,
            report_version=report.report_version,
            report_status=report.report_status,
            report_hash=report.report_hash,
            approved_by=report.approved_by,
            approved_at=report.approved_at.isoformat() if report.approved_at else None,
            released_by=report.released_by,
            released_at=report.released_at.isoformat() if report.released_at else None,
            amendment_reason=report.amendment_reason,
        ),
        "audit_timeline": timeline,
        "pdf_available": bool(report.pdf_path) and report.report_status in ("approved", "released", "amended"),
    }


def start_review(order_ref: str, *, actor: str | None = None) -> dict:
    detail = review_detail(order_ref)
    report = ClinicalReport.query.filter_by(report_code=detail["report"]["report_code"]).first()
    if report.report_status not in ("pending_review", "rejected"):
        if report.report_status != "in_review":
            raise ReportingEngineError(f"Cannot start review in status {report.report_status}")
    report.report_status = "in_review"
    report.updated_at = _utcnow()
    write_report_audit(action="doctor_review_started", object_type="clinical_report", object_id=report.report_code, actor=actor)
    return report.to_dict()


def _freeze_and_render_pdf(report: ClinicalReport, payload: dict[str, Any], *, actor: str | None) -> dict[str, Any]:
    """Freeze HTML + PDF from authoritative payload. PDF only after approval metadata set."""
    if not payload.get("items"):
        raise ReportingEngineError("Cannot generate report PDF without finalized result items")
    report_hash = generate_report_hash(payload)
    verify_url = build_verify_url(report.report_code, report_hash)
    qr = generate_qr_payload(report.report_code)
    html = render_html_report(
        payload,
        report_code=report.report_code,
        doctor_note=report.doctor_note,
        report_version=report.report_version,
        report_status=report.report_status,
        report_hash=report_hash,
        approved_by=report.approved_by,
        approved_at=report.approved_at.isoformat() if report.approved_at else None,
        released_by=report.released_by,
        released_at=report.released_at.isoformat() if report.released_at else None,
        amendment_reason=report.amendment_reason,
        verify_url=verify_url,
    )
    report.report_hash = report_hash
    report.qr_payload = qr
    report.html_content = html
    try:
        pdf_path = write_report_pdf(
            payload=payload,
            report_code=report.report_code,
            report_version=report.report_version,
            report_hash=report_hash,
            report_status=report.report_status,
            approved_by=report.approved_by,
            approved_at=report.approved_at,
            released_by=report.released_by,
            released_at=report.released_at,
            doctor_note=report.doctor_note,
            amendment_reason=report.amendment_reason,
            qr_payload=qr,
            verify_url=verify_url,
            reported_at=report.generated_at or report.approved_at,
        )
    except ReportPdfError as exc:
        raise ReportingEngineError(f"PDF generation failed: {exc}") from exc
    report.pdf_path = str(pdf_path)
    write_report_audit(action="report_pdf_generated", object_type="clinical_report", object_id=report.report_code, actor=actor)
    return prepare_pdf_payload(payload, html, pdf_ready=True, pdf_path=str(pdf_path))


def approve_report(order_ref: str, *, doctor_note: str | None = None, actor: str | None = None) -> dict:
    order = BizOrder.query.filter(or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)).first()
    if not order:
        raise ReportingEngineError("Order not found")
    report = ClinicalReport.query.filter_by(order_id=order.id).order_by(ClinicalReport.report_version.desc()).first()
    if not report:
        report = ensure_clinical_report(order)
    if report.report_status == "released":
        raise ReportingEngineError("Report already released")
    if report.report_status == "approved" and report.pdf_path:
        payload = build_report_payload(order.id)
        html = report.html_content or ""
        return {
            **report.to_dict(),
            "pdf_payload": prepare_pdf_payload(payload, html, pdf_ready=True, pdf_path=report.pdf_path),
        }

    result = BizResult.query.filter_by(order_id=order.id).first()
    already_approved = order.status in {ORDER_APPROVED, ORDER_RELEASED} or (
        result is not None and result.status in {RESULT_APPROVED, RESULT_RELEASED}
    )
    if not already_approved:
        biz.approve_result(order.order_code, doctor_note=doctor_note, actor=actor)
    elif doctor_note and result is not None:
        result.doctor_note = doctor_note

    payload = build_report_payload(order.id)
    report.doctor_note = doctor_note
    report.report_status = "approved"
    report.approved_by = actor or (result.approved_by if result else None)
    report.approved_at = _utcnow()
    report.generated_at = _utcnow()
    report.clinical_summary = doctor_note
    report.updated_at = _utcnow()

    pdf_payload = _freeze_and_render_pdf(report, payload, actor=actor)

    sig_hash = generate_report_hash({"report": report.report_code, "signer": actor, "at": report.approved_at.isoformat()})
    db.session.add(
        ReportDigitalSignature(
            report_id=report.id,
            signer_name=actor,
            signer_role="DOCTOR",
            signed_at=report.approved_at,
            signature_hash=sig_hash,
            report_hash=report.report_hash,
            signature_method="INTERNAL_APPROVAL",
        )
    )
    write_report_audit(action="report_approved", object_type="clinical_report", object_id=report.report_code, actor=actor)
    write_report_audit(action="report_signed", object_type="clinical_report", object_id=report.report_code, actor=actor)
    return {**report.to_dict(), "pdf_payload": pdf_payload}


def reject_report(order_ref: str, *, reason: str | None = None, actor: str | None = None) -> dict:
    order = BizOrder.query.filter(or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)).first()
    report = ClinicalReport.query.filter_by(order_id=order.id).order_by(ClinicalReport.report_version.desc()).first()
    if not report:
        raise ReportingEngineError("Report not found")
    report.report_status = "rejected"
    report.doctor_note = reason
    write_report_audit(action="report_rejected", object_type="clinical_report", object_id=report.report_code, actor=actor)
    return report.to_dict()


def request_repeat(order_ref: str, *, reason: str | None = None, actor: str | None = None) -> dict:
    report = reject_report(order_ref, reason=reason, actor=actor)
    write_report_audit(action="repeat_requested", object_type="clinical_report", object_id=report["report_code"], actor=actor)
    report["workflow"] = "lab_repeat_requested"
    return report


def release_report(order_ref: str, *, actor: str | None = None) -> dict:
    order = BizOrder.query.filter(or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)).first()
    if not order:
        raise ReportingEngineError("Order not found")
    report = ClinicalReport.query.filter_by(order_id=order.id).order_by(ClinicalReport.report_version.desc()).first()
    if not report:
        raise ReportingEngineError("Clinical report not found")
    if report.report_status != "approved":
        raise ReportingEngineError("Report must be approved before release")
    if not report.report_hash or not report.approved_at:
        raise ReportingEngineError("Report missing hash or approval timestamp")
    if not report.pdf_path:
        raise ReportingEngineError("Approved report missing PDF artifact")
    unresolved_critical = CriticalResultAlert.query.filter_by(order_id=order.id, status="new").count()
    if unresolved_critical:
        raise ReportingEngineError("Unresolved critical results require acknowledgement")

    biz.release_report(order.order_code, actor=actor)
    report.report_status = "released"
    report.released_by = actor
    report.released_at = _utcnow()
    report.is_visible_to_patient = True
    report.updated_at = _utcnow()

    # Refresh HTML for print consistency; keep immutable approved PDF bytes.
    try:
        payload = build_report_payload(order.id)
        report.html_content = render_html_report(
            payload,
            report_code=report.report_code,
            doctor_note=report.doctor_note,
            report_version=report.report_version,
            report_status=report.report_status,
            report_hash=report.report_hash,
            approved_by=report.approved_by,
            approved_at=report.approved_at.isoformat() if report.approved_at else None,
            released_by=report.released_by,
            released_at=report.released_at.isoformat() if report.released_at else None,
            amendment_reason=report.amendment_reason,
            verify_url=build_verify_url(report.report_code, report.report_hash),
        )
    except Exception:
        pass

    db.session.add(
        ReportNotificationEvent(
            event_type="report_released",
            recipient_type="patient",
            recipient_id=order.patient_code,
            channel="IN_APP",
            status="pending",
            report_id=report.id,
            payload_json=json.dumps({"report_code": report.report_code, "order_code": order.order_code}),
        )
    )
    write_report_audit(action="report_released", object_type="clinical_report", object_id=report.report_code, actor=actor)
    return report.to_dict()


def _reprint_count(report_code: str) -> int:
    return AuditLog.query.filter_by(action="report.report_reprinted", object_id=report_code).count()


def get_report_pdf(
    report_code: str,
    *,
    actor: str | None = None,
    as_reprint: bool = False,
    patient_code: str | None = None,
) -> dict[str, Any]:
    """Return PDF bytes for an approved/released report. Draft/pending denied."""
    report = ClinicalReport.query.filter_by(report_code=report_code).first()
    if not report:
        raise ReportingEngineError("Report not found")
    if report.report_status not in ("approved", "released", "amended"):
        raise ReportingEngineError("PDF available only after report approval")
    if patient_code is not None:
        if report.patient_id != patient_code or not is_report_visible_to_patient(report):
            raise ReportingEngineError("Report not visible to patient")
    if not report.pdf_path:
        # Amended originals may keep pdf; current version must have been approved with PDF
        path = resolve_pdf_path(report.report_code, report.report_version)
        if path.exists():
            report.pdf_path = str(path)
        else:
            raise ReportingEngineError("PDF artifact missing for report")

    try:
        data = read_pdf_bytes(report.pdf_path)
    except ReportPdfError as exc:
        raise ReportingEngineError(str(exc)) from exc

    reprint_number = 0
    if as_reprint:
        reprint_number = _reprint_count(report.report_code) + 1
        write_report_audit(
            action="report_reprinted",
            object_type="clinical_report",
            object_id=report.report_code,
            actor=actor,
        )

    filename = f"DxCon_{report.report_code}_v{report.report_version}.pdf"
    if reprint_number:
        filename = f"DxCon_{report.report_code}_v{report.report_version}_reprint{reprint_number}.pdf"

    return {
        "report_code": report.report_code,
        "report_version": report.report_version,
        "report_hash": report.report_hash,
        "report_status": report.report_status,
        "pdf_path": report.pdf_path,
        "filename": filename,
        "content_type": "application/pdf",
        "bytes": data,
        "reprint_number": reprint_number,
        "template_id": REPORT_PDF_TEMPLATE_ID,
        "template_version": REPORT_PDF_TEMPLATE_VERSION,
        "immutable": True,
    }


def verify_clinical_report(report_code: str, *, hash_prefix: str | None = None) -> dict[str, Any]:
    """Public verification of report authenticity (no PHI beyond minimal certificate fields)."""
    report = ClinicalReport.query.filter_by(report_code=report_code).first()
    if not report:
        return {"valid": False, "reason": "Report not found"}
    if report.report_status not in ("approved", "released", "amended"):
        return {"valid": False, "reason": "Report not finalized", "report_status": report.report_status}
    if hash_prefix and report.report_hash and not report.report_hash.startswith(hash_prefix):
        return {"valid": False, "reason": "Hash mismatch"}
    return {
        "valid": True,
        "report_code": report.report_code,
        "report_version": report.report_version,
        "report_status": report.report_status,
        "report_hash": report.report_hash,
        "approved_at": report.approved_at.isoformat() if report.approved_at else None,
        "released_at": report.released_at.isoformat() if report.released_at else None,
        "order_code": report.order_code,
        "template_id": REPORT_PDF_TEMPLATE_ID,
        "template_version": REPORT_PDF_TEMPLATE_VERSION,
        "pdf_available": bool(report.pdf_path),
        "qr_payload": report.qr_payload,
    }


def production_report_pdf_report() -> dict[str, Any]:
    approved_with_pdf = ClinicalReport.query.filter(
        ClinicalReport.report_status.in_(("approved", "released")),
        ClinicalReport.pdf_path.isnot(None),
    ).count()
    return {
        "report": "PRODUCTION_REPORT_PDF",
        "template_id": REPORT_PDF_TEMPLATE_ID,
        "template_version": REPORT_PDF_TEMPLATE_VERSION,
        "approved_or_released_with_pdf": approved_with_pdf,
        "total_clinical_reports": ClinicalReport.query.count(),
    }

def create_report_amendment(report_code: str, *, reason: str, actor: str | None = None) -> dict:
    original = ClinicalReport.query.filter_by(report_code=report_code).first()
    if not original:
        raise ReportingEngineError("Report not found")
    if original.report_status not in ("approved", "released"):
        raise ReportingEngineError("Only approved/released reports can be amended")
    original.report_status = "amended"
    new_report = ClinicalReport(
        report_code=generate_report_code(),
        order_id=original.order_id,
        order_code=original.order_code,
        patient_id=original.patient_id,
        accession_number=original.accession_number,
        report_status="pending_review",
        report_version=original.report_version + 1,
        amended_from_report_id=original.id,
        amendment_reason=reason,
    )
    db.session.add(new_report)
    write_report_audit(action="report_amended", object_type="clinical_report", object_id=new_report.report_code, actor=actor)
    return new_report.to_dict()


def report_versions(report_code: str) -> list[dict]:
    report = ClinicalReport.query.filter_by(report_code=report_code).first()
    if not report:
        return []
    chain = ClinicalReport.query.filter_by(order_id=report.order_id).order_by(ClinicalReport.report_version.asc()).all()
    return [{"version": r.report_version, **r.to_dict()} for r in chain]


def search_reports(
    *,
    patient: str | None = None,
    order_code: str | None = None,
    report_code: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 25,
) -> dict:
    query = ClinicalReport.query
    if patient:
        query = query.filter(ClinicalReport.patient_id.ilike(f"%{patient}%"))
    if order_code:
        query = query.filter(ClinicalReport.order_code.ilike(f"%{order_code}%"))
    if report_code:
        query = query.filter(ClinicalReport.report_code.ilike(f"%{report_code}%"))
    if status:
        query = query.filter_by(report_status=status)
    total = query.count()
    rows = query.order_by(ClinicalReport.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return {"data": [r.to_dict() for r in rows], "pagination": {"page": page, "per_page": per_page, "total": total}}


def audit_timeline(report_code: str) -> list[dict]:
    report = ClinicalReport.query.filter_by(report_code=report_code).first()
    if not report:
        return []
    events = []
    order = BizOrder.query.get(report.order_id)
    if order:
        audits = BizWorkflowAudit.query.filter(
            or_(
                BizWorkflowAudit.entity_id == order.order_code,
                BizWorkflowAudit.entity_id == report.report_code,
            )
        ).order_by(BizWorkflowAudit.created_at.asc()).all()
        for a in audits:
            events.append({"action": a.action, "status": a.new_status, "time": a.created_at.isoformat() if a.created_at else None, "actor": a.actor})
    from app.models.audit_log import AuditLog

    for log in AuditLog.query.filter(AuditLog.object_id.in_([report.report_code, order.order_code if order else ""])).limit(20):
        events.append({"action": log.action, "time": log.created_at.isoformat() if log.created_at else None, "actor": log.user_email})
    return events


def acknowledge_critical(alert_id: str, *, actor: str | None = None, note: str | None = None) -> dict:
    alert = CriticalResultAlert.query.get(alert_id)
    if not alert:
        raise ReportingEngineError("Alert not found")
    alert.status = "acknowledged"
    alert.acknowledged_by = actor
    alert.acknowledged_at = _utcnow()
    alert.note = note
    write_report_audit(action="critical_result_acknowledged", object_type="critical_alert", object_id=alert_id, actor=actor)
    return alert.to_dict()


def patient_released_reports(patient_code: str) -> list[dict]:
    reports = ClinicalReport.query.filter_by(
        patient_id=patient_code,
        report_status="released",
        is_visible_to_patient=True,
    ).all()
    return [r.to_dict() for r in reports]


def is_report_visible_to_patient(report: ClinicalReport) -> bool:
    return report.report_status == "released" and bool(report.is_visible_to_patient)


def reporting_engine_report() -> dict:
    return {
        "report": "REPORTING_ENGINE_REPORT",
        "clinical_reports": ClinicalReport.query.count(),
        "pending_review": ClinicalReport.query.filter_by(report_status="pending_review").count(),
        "released": ClinicalReport.query.filter_by(report_status="released").count(),
    }


def doctor_review_report() -> dict:
    return {
        "report": "DOCTOR_REVIEW_REPORT",
        "queue": ClinicalReport.query.filter(ClinicalReport.report_status.in_(("pending_review", "in_review"))).count(),
        "approved": ClinicalReport.query.filter_by(report_status="approved").count(),
    }


def report_security_report() -> dict:
    from app.core.permissions import role_has_permission

    return {
        "report": "REPORT_SECURITY_REPORT",
        "doctor_can_approve": role_has_permission("DOCTOR", "report.approve"),
        "reception_cannot_approve": not role_has_permission("RECEPTION", "report.approve"),
        "patient_released_only": True,
        "auto_release_disabled": True,
    }


def critical_result_report() -> dict:
    return {
        "report": "CRITICAL_RESULT_REPORT",
        "new_alerts": CriticalResultAlert.query.filter_by(status="new").count(),
        "acknowledged": CriticalResultAlert.query.filter_by(status="acknowledged").count(),
    }
