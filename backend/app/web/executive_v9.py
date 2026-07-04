
from flask import Blueprint

from app.web.demo_pilot_lib import render_safe_page
from app.web.pilot_dashboard_data import build_executive_body

executive_v9_bp = Blueprint("executive_v9", __name__)


@executive_v9_bp.route("/executive-v9")
def executive_v9():
    return render_safe_page(
        "Executive Dashboard",
        "Pilot Phase 3A operational overview with live system probes.",
        build_executive_body,
    )
