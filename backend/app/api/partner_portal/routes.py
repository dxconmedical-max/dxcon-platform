from flask import Blueprint, request

from app.services.partner_portal_service import (
    PartnerDashboardService,
    PartnerOrderService,
    PartnerPortalError,
    PartnerResultUploadService,
    PartnerRevenueService,
    PartnerSLAService,
)


partner_portal_bp = Blueprint(
    "partner_portal",
    __name__,
    url_prefix="/api/v1/partner-portal",
)


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


@partner_portal_bp.route("/dashboard", methods=["GET"])
def partner_dashboard():
    partner_id = request.args.get("partner_id")
    if not partner_id:
        return {"error": "partner_id is required"}, 400
    try:
        payload = PartnerDashboardService.get_dashboard(partner_id)
    except PartnerPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@partner_portal_bp.route("/orders", methods=["GET"])
def partner_orders():
    partner_id = request.args.get("partner_id")
    if not partner_id:
        return {"error": "partner_id is required"}, 400
    orders = PartnerOrderService.list_orders(partner_id, status=request.args.get("status"))
    return {"count": len(orders), "orders": orders}


@partner_portal_bp.route("/orders/<order_id>", methods=["GET"])
def partner_order_detail(order_id):
    partner_id = request.args.get("partner_id")
    if not partner_id:
        return {"error": "partner_id is required"}, 400
    try:
        payload = PartnerOrderService.get_order(partner_id, order_id)
    except PartnerPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@partner_portal_bp.route("/results/upload", methods=["POST"])
def upload_result():
    data = request.get_json(silent=True) or {}
    partner_id = data.get("partner_id")
    if not partner_id:
        return {"error": "partner_id is required"}, 400
    try:
        result = PartnerResultUploadService.upload_result(
            partner_id,
            data,
            actor_email=_actor_email(),
        )
    except PartnerPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return {"message": "Result uploaded", "result": result.to_dict()}, 201


@partner_portal_bp.route("/results", methods=["GET"])
def list_results():
    partner_id = request.args.get("partner_id")
    if not partner_id:
        return {"error": "partner_id is required"}, 400
    results = PartnerResultUploadService.list_results(partner_id)
    return {"count": len(results), "results": [r.to_dict() for r in results]}


@partner_portal_bp.route("/revenue", methods=["GET"])
def partner_revenue():
    partner_id = request.args.get("partner_id")
    if not partner_id:
        return {"error": "partner_id is required"}, 400
    return PartnerRevenueService.get_revenue_summary(partner_id)


@partner_portal_bp.route("/sla", methods=["GET"])
def partner_sla():
    partner_id = request.args.get("partner_id")
    if not partner_id:
        return {"error": "partner_id is required"}, 400
    try:
        payload = PartnerSLAService.get_sla_summary(partner_id)
    except PartnerPortalError as exc:
        return {"error": exc.message}, exc.status_code
    return payload
