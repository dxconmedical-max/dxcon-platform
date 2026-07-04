from flask import Blueprint

from app.utils.auth import role_required
from app.web.demo_pilot_lib import render_pilot_page
from app.web.pilot_dashboard_data import build_executive_body

executive_web_bp = Blueprint("executive_web", __name__)


@executive_web_bp.route("/executive")
@role_required("SUPER_ADMIN")
def executive():
    return render_pilot_page("Executive Dashboard", build_executive_body())
