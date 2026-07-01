from flask import Blueprint, request

from app.services.ai_cds_service import (
    AIInterpretationService,
    AIRecommendationService,
    AIRiskService,
    CDSError,
    ClinicalRuleEngineService,
    CriticalDetectionService,
)
from app.services.ai_interpretation import interpret_result as legacy_interpret


ai_cds_bp = Blueprint(
    "ai_cds",
    __name__,
    url_prefix="/api/v1/ai",
)


def _error(exc):
    return {"error": exc.message}, exc.status_code


@ai_cds_bp.route("/interpret", methods=["POST"])
def interpret():
    data = request.get_json(silent=True) or {}
    if data.get("legacy"):
        interpretation = legacy_interpret(
            data.get("test_name"),
            data.get("result_value"),
            data.get("reference_range"),
            data.get("flag"),
        )
        return {
            "test_name": data.get("test_name"),
            "result_value": data.get("result_value"),
            "reference_range": data.get("reference_range"),
            "flag": data.get("flag"),
            "interpretation": interpretation,
        }
    try:
        return AIInterpretationService.interpret_payload(data)
    except CDSError as exc:
        return _error(exc)


@ai_cds_bp.route("/risk", methods=["POST"])
def risk():
    data = request.get_json(silent=True) or {}
    if not data.get("items"):
        return {"error": "items is required"}, 400
    return AIRiskService.assess(data)


@ai_cds_bp.route("/recommend", methods=["POST"])
def recommend():
    data = request.get_json(silent=True) or {}
    if not data.get("items") and not data.get("lab_result_id"):
        return {"error": "items or lab_result_id is required"}, 400
    try:
        return AIRecommendationService.generate(data)
    except CDSError as exc:
        return _error(exc)


@ai_cds_bp.route("/reference-ranges", methods=["GET"])
def reference_ranges():
    return {
        "ranges": ClinicalRuleEngineService.list_reference_ranges(
            test_code=request.args.get("test_code"),
            sex=request.args.get("sex"),
            age=request.args.get("age"),
        )
    }


@ai_cds_bp.route("/critical-results", methods=["POST"])
def critical_results():
    data = request.get_json(silent=True) or {}
    if not data.get("items"):
        return {"error": "items is required"}, 400
    return CriticalDetectionService.detect(data)
