"""Population Health web routes — Phase 7.8."""

from __future__ import annotations

from flask import Blueprint

from app.services.population_health_service import POPULATION_HEALTH_ROLES
from app.utils.auth import role_required
from app.web.population_health_lib import (
    build_dashboard_body,
    build_disease_registry_body,
    build_population_dashboard_body,
    build_risk_groups_body,
    build_vaccination_statistics_body,
    build_diabetes_panel_body,
    build_hypertension_panel_body,
    build_cancer_panel_body,
    build_womens_health_panel_body,
    build_children_panel_body,
    render_hub_page,
)

population_health_web_bp = Blueprint("population_health_web", __name__)

@population_health_web_bp.route("/population-health")
@role_required(*POPULATION_HEALTH_ROLES)
def population_health_dashboard():
    return render_hub_page("Population Health", build_dashboard_body())
@population_health_web_bp.route("/population-health/registry")
@role_required(*POPULATION_HEALTH_ROLES)
def population_health_disease_registry():
    return render_hub_page("Disease Registry", build_disease_registry_body())
@population_health_web_bp.route("/population-health/dashboard")
@role_required(*POPULATION_HEALTH_ROLES)
def population_health_population_dashboard():
    return render_hub_page("Population Dashboard", build_population_dashboard_body())
@population_health_web_bp.route("/population-health/risk-groups")
@role_required(*POPULATION_HEALTH_ROLES)
def population_health_risk_groups():
    return render_hub_page("Risk Groups", build_risk_groups_body())
@population_health_web_bp.route("/population-health/vaccination")
@role_required(*POPULATION_HEALTH_ROLES)
def population_health_vaccination_statistics():
    return render_hub_page("Vaccination Statistics", build_vaccination_statistics_body())
@population_health_web_bp.route("/population-health/diabetes")
@role_required(*POPULATION_HEALTH_ROLES)
def population_health_diabetes_panel():
    return render_hub_page("Diabetes", build_diabetes_panel_body())
@population_health_web_bp.route("/population-health/hypertension")
@role_required(*POPULATION_HEALTH_ROLES)
def population_health_hypertension_panel():
    return render_hub_page("Hypertension", build_hypertension_panel_body())
@population_health_web_bp.route("/population-health/cancer")
@role_required(*POPULATION_HEALTH_ROLES)
def population_health_cancer_panel():
    return render_hub_page("Cancer", build_cancer_panel_body())
@population_health_web_bp.route("/population-health/womens-health")
@role_required(*POPULATION_HEALTH_ROLES)
def population_health_womens_health_panel():
    return render_hub_page("Women's Health", build_womens_health_panel_body())
@population_health_web_bp.route("/population-health/children")
@role_required(*POPULATION_HEALTH_ROLES)
def population_health_children_panel():
    return render_hub_page("Children", build_children_panel_body())

