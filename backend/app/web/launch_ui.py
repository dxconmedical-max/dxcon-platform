"""Launch UI Sprint 1 — product shell and role dashboards."""

from __future__ import annotations

from flask import Blueprint, redirect

from app.utils.auth import login_required
from app.web.launch_ui_lib import (
    collector_dashboard_body,
    doctor_dashboard_body,
    executive_dashboard_body,
    lab_dashboard_body,
    patient_dashboard_body,
    reception_dashboard_body,
    render_marketing_home,
    render_page,
    system_dashboard_body,
)

launch_ui_bp = Blueprint("launch_ui", __name__)


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
    return render_page("Executive Dashboard", executive_dashboard_body())


@launch_ui_bp.route("/app/reception")
@login_required
def app_reception():
    return render_page("Reception Dashboard", reception_dashboard_body())


@launch_ui_bp.route("/app/doctor")
@login_required
def app_doctor():
    return render_page("Doctor Workbench", doctor_dashboard_body())


@launch_ui_bp.route("/app/lab")
@login_required
def app_lab():
    return render_page("Lab Dashboard", lab_dashboard_body())


@launch_ui_bp.route("/app/collector")
@login_required
def app_collector():
    return render_page("Collector Dashboard", collector_dashboard_body())


@launch_ui_bp.route("/app/patient")
@login_required
def app_patient():
    return render_page("Patient Portal", patient_dashboard_body())


@launch_ui_bp.route("/app/system")
@login_required
def app_system():
    return render_page("System Center", system_dashboard_body())
