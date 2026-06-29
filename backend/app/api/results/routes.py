from flask import Blueprint, request

from app.services.result_gateway_service import (
    ResultApprovalService,
    ResultGatewayError,
    ResultGatewayBase,
    ResultReleaseService,
    ResultReviewService,
    ResultUploadService,
    ResultValidationService,
)


results_bp = Blueprint(
    "results_gateway",
    __name__,
    url_prefix="/api/v1/results",
)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


@results_bp.route("", methods=["GET"])
def list_results():
    results = ResultGatewayBase.list_results(
        status=request.args.get("status"),
        medical_order_id=request.args.get("medical_order_id"),
    )
    return {
        "count": len(results),
        "results": [result.to_dict(include_items=True) for result in results],
    }


@results_bp.route("/upload", methods=["POST"])
def upload_result():
    data = request.get_json(silent=True) or {}
    try:
        result = ResultUploadService.upload_analyzer(
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
        validated = ResultValidationService.validate(
            result.id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except ResultGatewayError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Analyzer result uploaded",
        "result": validated.to_dict(include_items=True, include_attachments=True),
    }, 201


@results_bp.route("/manual", methods=["POST"])
def manual_result():
    data = request.get_json(silent=True) or {}
    try:
        result = ResultUploadService.create_manual(
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
        validated = ResultValidationService.validate(
            result.id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except ResultGatewayError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Manual result created",
        "result": validated.to_dict(include_items=True, include_attachments=True),
    }, 201


@results_bp.route("/<result_id>", methods=["GET"])
def get_result(result_id):
    try:
        payload = ResultGatewayBase.get_result_detail(result_id)
    except ResultGatewayError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@results_bp.route("/<result_id>/review", methods=["POST"])
def review_result(result_id):
    data = request.get_json(silent=True) or {}
    try:
        result, review = ResultReviewService.submit_review(
            result_id,
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except ResultGatewayError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Result submitted for review",
        "result": result.to_dict(include_items=True),
        "review": review.to_dict(),
    }


@results_bp.route("/<result_id>/approve", methods=["POST"])
def approve_result(result_id):
    data = request.get_json(silent=True) or {}
    try:
        result = ResultApprovalService.approve(
            result_id,
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except ResultGatewayError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Result approved",
        "result": result.to_dict(include_items=True),
    }


@results_bp.route("/<result_id>/release", methods=["POST"])
def release_result(result_id):
    data = request.get_json(silent=True) or {}
    try:
        result, release = ResultReleaseService.release(
            result_id,
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except ResultGatewayError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Result released",
        "result": result.to_dict(include_items=True, include_attachments=True),
        "release": release.to_dict(),
    }


@results_bp.route("/<result_id>/timeline", methods=["GET"])
def result_timeline(result_id):
    try:
        timeline = ResultGatewayBase.get_timeline(result_id)
    except ResultGatewayError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "count": len(timeline),
        "timeline": [entry.to_dict() for entry in timeline],
    }
