from flask import Blueprint, request

from app.services.interpretation_engine_service import (
    CriticalValueService,
    InterpretationEngine,
    InterpretationError,
    ReferenceRangeService,
)


interpretation_bp = Blueprint(
    "interpretation",
    __name__,
    url_prefix="/api/v1/interpretation",
)

reference_ranges_bp = Blueprint(
    "reference_ranges",
    __name__,
    url_prefix="/api/v1/reference-ranges",
)


@interpretation_bp.route("/rules", methods=["GET"])
def list_rules():
    rules = InterpretationEngine.list_rules()
    templates = InterpretationEngine.list_templates()
    return {
        "rules_count": len(rules),
        "templates_count": len(templates),
        "rules": [rule.to_dict() for rule in rules],
        "templates": [template.to_dict() for template in templates],
        "critical_rules": [rule.to_dict() for rule in CriticalValueService.list_rules()],
    }


@interpretation_bp.route("/run", methods=["POST"])
def run_interpretation():
    data = request.get_json(silent=True) or {}
    lab_result_id = data.get("lab_result_id")
    if not lab_result_id:
        return {"error": "lab_result_id is required"}, 400
    try:
        rows = InterpretationEngine.run(
            lab_result_id,
            patient_age=data.get("patient_age"),
            patient_sex=data.get("patient_sex"),
        )
    except InterpretationError as exc:
        return {"error": exc.message}, exc.status_code
    language = data.get("language")
    return {
        "message": "Interpretation completed",
        "count": len(rows),
        "interpretations": [row.to_dict(language=language) for row in rows],
    }, 201


@interpretation_bp.route("/<result_id>", methods=["GET"])
def get_interpretation(result_id):
    try:
        payload = InterpretationEngine.get_for_result(
            result_id,
            language=request.args.get("language"),
        )
    except InterpretationError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@reference_ranges_bp.route("", methods=["GET"])
def list_reference_ranges():
    ranges = ReferenceRangeService.list_ranges(
        test_code=request.args.get("test_code"),
        sex=request.args.get("sex"),
    )
    return {
        "count": len(ranges),
        "reference_ranges": [row.to_dict() for row in ranges],
    }
