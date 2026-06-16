from flask import Blueprint, request, jsonify

from app.services.ai_interpretation import interpret_result


ai_bp = Blueprint(
    "ai",
    __name__,
    url_prefix="/api/v1/ai"
)


@ai_bp.route("/interpret", methods=["POST"])
def interpret():

    data = request.get_json() or {}

    interpretation = interpret_result(
        data.get("test_name"),
        data.get("result_value"),
        data.get("reference_range"),
        data.get("flag")
    )

    return jsonify({
        "test_name": data.get("test_name"),
        "result_value": data.get("result_value"),
        "reference_range": data.get("reference_range"),
        "flag": data.get("flag"),
        "interpretation": interpretation
    })
