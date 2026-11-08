"""Read-only lookup of RELEASED reports for a clinic (tenant), scoped by the caller's own organization."""

from __future__ import annotations

from flask import Blueprint, request

from app.business_engine.statuses import RESULT_RELEASED
from app.core.audit import write_audit
from app.core.authenticated_identity import (
    AuthenticatedIdentity,
    authenticated_actor_email,
    bind_authenticated_identity,
)
from app.core.errors import build_error_response
from app.core.tenant_authorization import AuthorizedTenant, resolve_authorized_tenant
from app.extensions.db import db
from app.models.biz_order import BizOrder, BizResult

clinic_results_bp = Blueprint("clinic_results", __name__, url_prefix="/api/v1/clinic-results")


@clinic_results_bp.before_request
def _require_authenticated_user():
    # CORS preflight (OPTIONS) never carries credentials; letting it through is what
    # allows the browser to send the real request. All other methods require a login.
    if request.method == "OPTIONS":
        return None
    result = bind_authenticated_identity()
    if not isinstance(result, AuthenticatedIdentity):
        return result
    return None


def _org():
    tenant = resolve_authorized_tenant(require_scope=True)
    if not isinstance(tenant, AuthorizedTenant):
        return None, tenant
    if not tenant.organization_id:
        return None, build_error_response("BAD_REQUEST", "organization is required", 400)
    return tenant.organization_id, None


def _int_arg(name: str, default: int, low: int, high: int) -> int:
    try:
        value = int(request.args.get(name, default))
    except (TypeError, ValueError):
        value = default
    return max(low, min(high, value))


def _released(org_id: str):
    return (
        db.session.query(BizOrder, BizResult)
        .join(BizResult, BizResult.order_id == BizOrder.id)
        .filter(
            BizOrder.organization_id == org_id,
            BizResult.patient_visible.is_(True),
            BizResult.status == RESULT_RELEASED,
        )
    )


def _audit_access(action: str, org_id: str, ref: str) -> None:
    """Record who looked at clinic results. Raises on failure so nothing is shown without a log entry."""
    write_audit(
        action,
        "ClinicReport",
        f"{ref}|org={org_id}",
        user_email=authenticated_actor_email(),
        ip_address=(request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or request.remote_addr or "")[:100],
    )
    db.session.commit()


def _not_found():
    return build_error_response("NOT_FOUND", "Report not found", 404)


@clinic_results_bp.route("/reports", methods=["GET"])
def list_reports():
    org_id, err = _org()
    if err is not None:
        return err
    limit = _int_arg("limit", 50, 1, 100)
    page = _int_arg("page", 1, 1, 100000)
    query = _released(org_id)
    total = query.count()
    rows = query.order_by(BizResult.released_at.desc()).offset((page - 1) * limit).limit(limit).all()
    data = [
        {
            "order_code": order.order_code,
            "result_code": result.result_code,
            "patient_code": order.patient_code,
            "patient_name": order.patient_name,
            "released_at": result.released_at.isoformat() if result.released_at else None,
        }
        for order, result in rows
    ]
    _audit_access("CLINIC_REPORT_LIST", org_id, f"page={page}")
    return {"success": True, "data": data, "pagination": {"page": page, "per_page": limit, "total": total}}, 200


@clinic_results_bp.route("/reports/<order_code>", methods=["GET"])
def get_report(order_code: str):
    org_id, err = _org()
    if err is not None:
        return err
    row = _released(org_id).filter(BizOrder.order_code == order_code).first()
    if row is None:
        return _not_found()
    from app.lab_workspace.service import LabWorkspaceError, get_released_report_html

    try:
        detail = get_released_report_html(order_code)
    except LabWorkspaceError:
        return _not_found()
    order, result = row
    _audit_access("CLINIC_REPORT_VIEW", org_id, order.order_code)
    payload = {
        "success": True,
        "data": {
            "order_code": order.order_code,
            "result_code": result.result_code,
            "patient_code": order.patient_code,
            "patient_name": order.patient_name,
            "released_at": result.released_at.isoformat() if result.released_at else None,
            "html_content": detail["html_content"],
        },
    }
    return payload, 200, {"Cache-Control": "no-store"}
