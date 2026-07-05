"""Launch UI — product shell, role dashboards, and functional module pages."""

from __future__ import annotations

from flask import Blueprint, redirect

from app.utils.auth import login_required
from app.web.launch_ui_lib import (
    collector_dashboard_body,
    doctor_dashboard_body,
    executive_dashboard_body,
    patient_dashboard_body,
    render_marketing_home,
    render_page,
    system_dashboard_body,
)
from app.web.launch_ui_modules import DETAIL_ROUTE_BUILDERS, MODULE_SPECS
from app.web.launch_ui_actions import ACTION_SLUGS, handle_demo_action

launch_ui_bp = Blueprint("launch_ui", __name__)


def _module_view(path: str, title: str, body_fn):
    @login_required
    def view():
        parent = "/app/executive"
        if path.startswith("/app/patient/"):
            parent = "/app/patient"
        elif path.startswith("/app/lab/"):
            parent = "/app/lab"
        elif path.startswith("/app/reception/"):
            parent = "/app/reception"
        elif path.startswith("/app/samples") or path.startswith("/app/collections") or path == "/app/iot":
            parent = "/app/collector" if "collection" in path or path == "/app/iot" else "/app/lab"
        elif path in {"/app/orders", "/app/patients", "/app/reports", "/app/finance", "/app/logistics"}:
            parent = "/app/executive"
        elif path == "/app/ai":
            parent = "/app/doctor"
        return render_page(title, body_fn(), active_nav=parent)

    view.__name__ = f"launch_module_{path.strip('/').replace('/', '_')}"
    return view


def _detail_view(path_pattern: str, title_prefix: str, body_fn, active_nav: str):
    @login_required
    def view(**kwargs):
        key = next(iter(kwargs.values()))
        return render_page(title_prefix, body_fn(key), active_nav=active_nav)

    view.__name__ = f"launch_detail_{path_pattern.strip('/').replace('/', '_').replace('<', '').replace('>', '')}"
    return view


for _path, _title, _body_fn in MODULE_SPECS:
    launch_ui_bp.add_url_rule(_path, view_func=_module_view(_path, _title, _body_fn))

for _pattern, _body_fn in DETAIL_ROUTE_BUILDERS:
    _nav = "/app/executive"
    if "patients" in _pattern:
        _nav = "/app/patients"
    elif "orders" in _pattern:
        _nav = "/app/orders"
    elif "reports" in _pattern:
        _nav = "/app/reports"
    _title = {"patients": "Patient Profile", "orders": "Order Detail", "reports": "Report Detail"}
    label = next(v for k, v in _title.items() if k in _pattern)
    launch_ui_bp.add_url_rule(_pattern, view_func=_detail_view(_pattern, label, _body_fn, _nav))


def _action_view(slug: str):
    @login_required
    def view():
        body = handle_demo_action(slug)
        return render_page("Action complete", body, active_nav="/app/executive")

    view.__name__ = f"launch_action_{slug.replace('-', '_')}"
    return view


for _slug in ACTION_SLUGS:
    launch_ui_bp.add_url_rule(
        f"/app/actions/{_slug}",
        view_func=_action_view(_slug),
        methods=["GET", "POST"],
    )


@launch_ui_bp.route("/")
def root_redirect():
    return redirect("/login")


@launch_ui_bp.route("/home")
def marketing_home():
    return render_marketing_home()


@launch_ui_bp.route("/app/executive")
@launch_ui_bp.route("/executive-v10")
@login_required
def app_executive():
    return render_page("Executive Dashboard", executive_dashboard_body(), active_nav="/app/executive")


@launch_ui_bp.route("/app/doctor")
@login_required
def app_doctor():
    return render_page("Doctor Workbench", doctor_dashboard_body(), active_nav="/app/doctor")


@launch_ui_bp.route("/app/collector")
@login_required
def app_collector():
    return render_page("Collector Dashboard", collector_dashboard_body(), active_nav="/app/collector")


@launch_ui_bp.route("/app/patient")
@login_required
def app_patient():
    return render_page("Patient Portal", patient_dashboard_body(), active_nav="/app/patient")


@launch_ui_bp.route("/app/system")
@login_required
def app_system():
    return render_page("System Center", system_dashboard_body(), active_nav="/app/system")
