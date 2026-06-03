from flask import Blueprint, request

from app.services.ai_interpretation import interpret_result

ai_bp = Blueprint(
    "ai",
    __name__,
    url_prefix="/api/v1/ai"
)


@ai_bp.route("/interpret", methods=["POST"])
def interpret():

    data = request.get_json()

    result = interpret_result(
        data.get("test_name"),
        data.get("value")
    )

    return result
