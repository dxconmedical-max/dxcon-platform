"""Reception desk demo dashboard for pilot workflow."""

from flask import Blueprint

from app.web.demo_pilot_lib import render_safe_page
from app.web.pilot_dashboard_data import build_reception_body

reception_web_bp = Blueprint("reception_web", __name__)


@reception_web_bp.route("/reception")
def reception_dashboard():
    return render_safe_page(
        "Reception Dashboard",
        "Front desk queue, appointments, registration, and payment status.",
        build_reception_body,
    )
