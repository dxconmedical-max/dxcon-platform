"""Clinical governance service — result consolidation, review, release safety."""

from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.analyzer_integration.service import list_preliminary_results
from app.clinical_governance.workflow import WorkflowError, record_transition, timeline
from app.core.statuses import (
    CLINICAL_REPORT_APPROVED,
    CLINICAL_REPORT_RELEASED,
    CLINICAL_RESULT_APPROVED,
    CLINICAL_RESULT_DOCTOR_REVIEW,
    CLINICAL_RESULT_PENDING,
    CLINICAL_RESULT_PRELIMINARY,
    CLINICAL_RESULT_REJECTED,
    CLINICAL_RESULT_RELEASED,
    CLINICAL_RESULT_TECHNICIAN_REVIEW,
    CLINICAL_RESULT_TECHNICIAN_REVIEW,
    CLINICAL_RESULT_TECHNICIAN_VALIDATED,
)
from app.extensions.db import db
from app.models.analyzer_integration import AnalyzerPreliminaryResult
from app.models.biz_order import BizOrder, BizResult, BizResultItem
from app.models.clinical_governance import (
    CriticalValueAcknowledgement,
    CriticalValuePolicy,
    ReportVerificationToken,
)
from app.models.clinical_report import ClinicalReport, CriticalResultAlert
from app.reporting_engine import service as reporting


class ClinicalGovernanceError(ValueError):
    pass


def _utcnow() -> datetime:
    return datetime.utcnow()


def technician_queue(*, organization_id: str) -> dict:
    prelim = list_preliminary_results(organization_id=organization_id, review_status="PENDING_REVIEW")
    items = BizResultItem.query.join(BizResult).filter(
        BizResultItem.result_status.in_([CLINICAL_RESULT_PRELIMINARY, CLINICAL_RESULT_TECHNICIAN_REVIEW, None, "PENDING"])
    ).all()
    return {
        "preliminary_analyzer": prelim.get("results", []),
        "result_items_pending": [_item_dict(i) for i in items if getattr(i, "result_status", None) != CLINICAL_RESULT_TECHNICIAN_VALIDATED],
    }


def _item_dict(item: BizResultItem) -> dict:
    d = item.to_dict()
    d["original_value"] = getattr(item, "original_value", None) or item.result_value
    d["normalized_value"] = getattr(item, "normalized_value", None) or item.result_value
    d["result_status"] = getattr(item, "result_status", "PENDING")
    d["critical_flag"] = getattr(item, "critical_flag", False)
    return d


def get_result_item(item_id: str, *, organization_id: str) -> dict:
    item = BizResultItem.query.get(item_id)
    if not item:
        raise ClinicalGovernanceError("Result item not found")
    result = BizResult.query.get(item.result_id)
    order = BizOrder.query.get(result.order_id) if result else None
    if order and hasattr(order, "organization_id") and order.organization_id and order.organization_id != organization_id:
        raise ClinicalGovernanceError("Tenant isolation violation")
    payload = _item_dict(item)
    if result:
        payload["order_code"] = order.order_code if order else None
        payload["timeline"] = timeline(organization_id=organization_id, aggregate_type="result", aggregate_id=item.id)
    return payload


def promote_preliminary_to_result(
    preliminary_id: str,
    *,
    organization_id: str,
    order_id: str,
    actor: str,
) -> dict:
    """Bridge Sprint 5 analyzer preliminary into biz result item — no auto-release."""
    prelim = AnalyzerPreliminaryResult.query.get(preliminary_id)
    if not prelim or prelim.organization_id != organization_id:
        raise ClinicalGovernanceError("Preliminary result not found")
    if prelim.review_status == "QUARANTINED":
        raise ClinicalGovernanceError("Cannot promote quarantined result")
    order = BizOrder.query.get(order_id)
    if not order:
        raise ClinicalGovernanceError("Order not found")
    result = BizResult.query.filter_by(order_id=order_id).first()
    if not result:
        result = BizResult(result_code=f"RES-{uuid.uuid4().hex[:8].upper()}", order_id=order_id, status="testing")
        db.session.add(result)
        db.session.flush()
    item = BizResultItem(
        result_id=result.id,
        test_code=prelim.test_code,
        test_name=prelim.test_code or "Test",
        result_value=prelim.normalized_value or prelim.original_value,
    )
    if hasattr(item, "original_value"):
        item.original_value = prelim.original_value
        item.normalized_value = prelim.normalized_value or prelim.original_value
        item.unit = prelim.unit
        item.result_status = CLINICAL_RESULT_PRELIMINARY
        item.preliminary_result_id = prelim.id
    db.session.add(item)
    db.session.flush()
    prelim.review_status = CLINICAL_RESULT_TECHNICIAN_REVIEW
    record_transition(
        organization_id=organization_id,
        aggregate_type="result",
        aggregate_id=item.id,
        from_status=CLINICAL_RESULT_PENDING,
        to_status=CLINICAL_RESULT_PRELIMINARY,
        actor=actor,
    )
    db.session.flush()
    return _item_dict(item)


def validate_result_item(item_id: str, *, organization_id: str, actor: str, note: str | None = None) -> dict:
    item = BizResultItem.query.get(item_id)
    if not item:
        raise ClinicalGovernanceError("Result item not found")
    current = getattr(item, "result_status", CLINICAL_RESULT_PRELIMINARY) or CLINICAL_RESULT_PRELIMINARY
    if current == CLINICAL_RESULT_RELEASED:
        raise ClinicalGovernanceError("Released results cannot be re-validated in place")
    if current in (CLINICAL_RESULT_PRELIMINARY, CLINICAL_RESULT_PENDING, "PENDING"):
        record_transition(
            organization_id=organization_id,
            aggregate_type="result",
            aggregate_id=item.id,
            from_status=current,
            to_status=CLINICAL_RESULT_TECHNICIAN_REVIEW,
            actor=actor,
            reason=note,
        )
        if hasattr(item, "result_status"):
            item.result_status = CLINICAL_RESULT_TECHNICIAN_REVIEW
        current = CLINICAL_RESULT_TECHNICIAN_REVIEW
    record_transition(
        organization_id=organization_id,
        aggregate_type="result",
        aggregate_id=item.id,
        from_status=current,
        to_status=CLINICAL_RESULT_TECHNICIAN_VALIDATED,
        actor=actor,
        reason=note,
    )
    if hasattr(item, "result_status"):
        item.result_status = CLINICAL_RESULT_TECHNICIAN_VALIDATED
        item.technician_reviewer = actor
        item.reviewed_at = _utcnow()
    _evaluate_critical(item, organization_id=organization_id)
    return _item_dict(item)


def reject_result_item(item_id: str, *, organization_id: str, actor: str, reason: str) -> dict:
    item = BizResultItem.query.get(item_id)
    if not item:
        raise ClinicalGovernanceError("Result item not found")
    current = getattr(item, "result_status", None)
    record_transition(
        organization_id=organization_id,
        aggregate_type="result",
        aggregate_id=item.id,
        from_status=current,
        to_status=CLINICAL_RESULT_REJECTED,
        actor=actor,
        reason=reason,
        exceptional=True,
    )
    if hasattr(item, "result_status"):
        item.result_status = CLINICAL_RESULT_REJECTED
    return _item_dict(item)


def request_rerun(item_id: str, *, organization_id: str, actor: str, reason: str) -> dict:
    item = BizResultItem.query.get(item_id)
    if not item:
        raise ClinicalGovernanceError("Result item not found")
    record_transition(
        organization_id=organization_id,
        aggregate_type="result",
        aggregate_id=item.id,
        from_status=getattr(item, "result_status", None),
        to_status=CLINICAL_RESULT_PRELIMINARY,
        actor=actor,
        reason=reason,
        exceptional=True,
    )
    if hasattr(item, "result_status"):
        item.result_status = CLINICAL_RESULT_PRELIMINARY
    return _item_dict(item)


def _evaluate_critical(item: BizResultItem, *, organization_id: str) -> None:
    policies = CriticalValuePolicy.query.filter_by(organization_id=organization_id, status="ACTIVE").all()
    val = float(item.normalized_value or item.result_value or 0) if (item.normalized_value or item.result_value) else None
    if val is None:
        return
    for policy in policies:
        if policy.test_code and policy.test_code != item.test_code:
            continue
        breach = False
        if policy.lower_threshold is not None and val < policy.lower_threshold:
            breach = True
        if policy.upper_threshold is not None and val > policy.upper_threshold:
            breach = True
        if breach:
            if hasattr(item, "critical_flag"):
                item.critical_flag = True
            item.flag = "CRITICAL"
            result = BizResult.query.get(item.result_id)
            order = BizOrder.query.get(result.order_id) if result else None
            db.session.add(
                CriticalResultAlert(
                    order_id=result.order_id if result else None,
                    order_code=order.order_code if order else "",
                    patient_id=order.patient_code if order else "UNKNOWN",
                    result_id=result.id if result else None,
                    critical_type="threshold_breach",
                    status="new",
                )
            )


def doctor_queue(**kwargs) -> dict:
    return reporting.review_queue(**{k: v for k, v in kwargs.items() if k in ("patient", "order_code", "critical_only", "status", "page", "per_page")})


def release_report_governed(
    order_ref: str,
    *,
    organization_id: str,
    actor: str,
) -> dict:
    """Explicit release — requires prior approval; never automatic."""
    order = BizOrder.query.filter(
        (BizOrder.order_code == order_ref) | (BizOrder.id == order_ref)
    ).first()
    if not order:
        raise ClinicalGovernanceError("Order not found")
    result = BizResult.query.filter_by(order_id=order.id).first()
    if result:
        for item in result.items:
            status = getattr(item, "result_status", None)
            if status and status not in (CLINICAL_RESULT_TECHNICIAN_VALIDATED, CLINICAL_RESULT_APPROVED, CLINICAL_RESULT_DOCTOR_REVIEW):
                raise ClinicalGovernanceError("Technician validation incomplete for one or more results")
    report = ClinicalReport.query.filter_by(order_id=order.id).order_by(ClinicalReport.report_version.desc()).first()
    if not report:
        raise ClinicalGovernanceError("Report not generated")
    if report.report_status not in ("approved", CLINICAL_REPORT_APPROVED):
        raise ClinicalGovernanceError("Doctor approval required before release")
    open_critical = CriticalResultAlert.query.filter_by(status="new").count()
    if open_critical > 0:
        raise ClinicalGovernanceError("Unresolved critical alerts must be acknowledged before release")
    payload = reporting.release_report(order_ref, actor=actor)
    token = create_verification_token(report, organization_id=organization_id)
    return {"release": payload, "verification_token": token["token"]}


def create_verification_token(report: ClinicalReport, *, organization_id: str) -> dict:
    token = secrets.token_urlsafe(32)
    row = ReportVerificationToken(
        organization_id=organization_id,
        report_id=report.id,
        report_code=report.report_code,
        token=token,
        report_version=report.report_version,
        report_hash=report.report_hash,
        expires_at=_utcnow() + timedelta(days=365),
    )
    db.session.add(row)
    return {"token": token, "report_code": report.report_code, "version": report.report_version}


def verify_report_token(token: str) -> dict:
    """Public verification — no PHI in response."""
    row = ReportVerificationToken.query.filter_by(token=token).first()
    if not row:
        return {"valid": False, "status": "NOT_FOUND"}
    if row.status != "ACTIVE" or (row.expires_at and row.expires_at < _utcnow()):
        return {"valid": False, "status": row.status, "report_code": row.report_code}
    report = ClinicalReport.query.get(row.report_id)
    return {
        "valid": True,
        "report_code": row.report_code,
        "report_version": row.report_version,
        "report_status": report.report_status if report else "unknown",
        "amended": bool(report and report.amended_from_report_id),
        "revoked": report.report_status == "revoked" if report else False,
        "message": "Report authenticity verified. Full clinical content available only to authorized users.",
    }


def acknowledge_critical(alert_id: str, *, organization_id: str, actor: str, method: str = "in_app") -> dict:
    alert = CriticalResultAlert.query.get(alert_id)
    if not alert:
        raise ClinicalGovernanceError("Alert not found")
    alert.status = "acknowledged"
    ack = CriticalValueAcknowledgement(
        organization_id=organization_id,
        alert_id=alert_id,
        acknowledged_by=actor,
        communication_method=method,
    )
    db.session.add(ack)
    return ack.to_dict()


def create_critical_policy(data: dict, *, organization_id: str, actor: str) -> dict:
    policy = CriticalValuePolicy(
        organization_id=organization_id,
        policy_code=data.get("policy_code") or f"CVP-{uuid.uuid4().hex[:6].upper()}",
        test_code=data.get("test_code"),
        analyte=data.get("analyte"),
        lower_threshold=data.get("lower_threshold"),
        upper_threshold=data.get("upper_threshold"),
        approved_by=actor,
        effective_at=_utcnow(),
    )
    db.session.add(policy)
    return policy.to_dict()
