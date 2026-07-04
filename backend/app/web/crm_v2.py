from flask import Blueprint

from app.web.demo_pilot_lib import render_safe_page
from app.web.pilot_dashboard_data import build_crm_body

crm_v2_web_bp = Blueprint("crm_v2_web", __name__)


@crm_v2_web_bp.route("/crm-pipeline")
def crm_pipeline():
    return render_safe_page(
        "CRM Dashboard",
        "Sales pipeline, follow-ups, and patient engagement for pilot operations.",
        build_crm_body,
    )
