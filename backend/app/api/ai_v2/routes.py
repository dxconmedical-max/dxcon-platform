from flask import Blueprint

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.test_result import TestResult
from app.models.clinical_summary import ClinicalSummary
from app.extensions.db import db


ai_interpret_v2_bp = Blueprint(
    "ai_interpret_v2",
    __name__,
    url_prefix="/api/v1/ai-v2"
)


def interpret_result(result):

    name = (result.test_name or "").lower()
    value = str(result.result_value or "")
    flag = (result.flag or "").upper()

    if "hba1c" in name and flag == "HIGH":
        return {
            "risk": "MEDIUM",
            "finding": "HbA1c is above reference range, suggesting possible impaired glucose control.",
            "recommendation": "Recommend dietary control, exercise, and repeat HbA1c follow-up."
        }

    if "glucose" in name and flag == "HIGH":
        return {
            "risk": "MEDIUM",
            "finding": "Glucose is above reference range.",
            "recommendation": "Recommend fasting glucose confirmation and clinical correlation."
        }

    if "lipid" in name and flag == "HIGH":
        return {
            "risk": "MEDIUM",
            "finding": "Lipid profile is abnormal.",
            "recommendation": "Recommend cardiovascular risk assessment and lifestyle modification."
        }

    if flag == "HIGH":
        return {
            "risk": "LOW",
            "finding": f"{result.test_name} is above reference range.",
            "recommendation": "Recommend clinical correlation and follow-up if symptoms persist."
        }

    return {
        "risk": "LOW",
        "finding": f"{result.test_name} is within expected range.",
        "recommendation": "Continue routine monitoring."
    }


@ai_interpret_v2_bp.route("/order/<order_id>")
def ai_order(order_id):

    order = Order.query.get(order_id)

    if not order:
        return {"error": "order not found"}, 404

    order_items = OrderItem.query.filter_by(
        order_id=order.id
    ).all()

    findings = []
    recommendations = []
    risk_level = "LOW"

    for item in order_items:

        result = TestResult.query.filter_by(
            order_item_id=item.id
        ).first()

        if not result:
            continue

        analysis = interpret_result(result)

        findings.append(analysis["finding"])
        recommendations.append(analysis["recommendation"])

        if analysis["risk"] in ["HIGH", "CRITICAL"]:
            risk_level = analysis["risk"]
        elif analysis["risk"] == "MEDIUM" and risk_level == "LOW":
            risk_level = "MEDIUM"

    summary = ClinicalSummary.query.filter_by(
        order_id=order.id
    ).first()

    if not summary:
        summary = ClinicalSummary(
            order_id=order.id
        )
        db.session.add(summary)

    summary.risk_level = risk_level
    summary.findings = "\\n".join(findings) if findings else "No significant abnormal laboratory pattern detected."
    summary.recommendations = "\\n".join(recommendations) if recommendations else "Continue routine monitoring."

    db.session.commit()

    return {
        "success": True,
        "order_id": order.id,
        "risk_level": summary.risk_level,
        "findings": summary.findings,
        "recommendations": summary.recommendations
    }
