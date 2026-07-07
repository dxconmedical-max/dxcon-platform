"""Population Health API routes — Phase 7.8."""

from __future__ import annotations

from flask import Blueprint

from app.services.population_health_service import (
    dashboard_payload,
    disease_registry,
    population_dashboard,
    risk_groups,
    vaccination_statistics,
    diabetes_panel,
    hypertension_panel,
    cancer_panel,
    womens_health_panel,
    children_panel,
    population_health_readiness_report,
)

population_health_bp = Blueprint("population_health_api", __name__, url_prefix="/api/v1/population-health")

@population_health_bp.route("/dashboard", methods=["GET"])
def population_health_dashboard_api():
    payload = dashboard_payload()
    payload["population"] = population_dashboard()
    return payload

@population_health_bp.route("/registry", methods=["GET"])
def population_health_disease_registry_api():
    return disease_registry()

@population_health_bp.route("/risk-groups", methods=["GET"])
def population_health_risk_groups_api():
    return risk_groups()

@population_health_bp.route("/vaccination", methods=["GET"])
def population_health_vaccination_statistics_api():
    return vaccination_statistics()

@population_health_bp.route("/diabetes", methods=["GET"])
def population_health_diabetes_panel_api():
    return diabetes_panel()

@population_health_bp.route("/hypertension", methods=["GET"])
def population_health_hypertension_panel_api():
    return hypertension_panel()

@population_health_bp.route("/cancer", methods=["GET"])
def population_health_cancer_panel_api():
    return cancer_panel()

@population_health_bp.route("/womens-health", methods=["GET"])
def population_health_womens_health_panel_api():
    return womens_health_panel()

@population_health_bp.route("/children", methods=["GET"])
def population_health_children_panel_api():
    return children_panel()

@population_health_bp.route("/readiness", methods=["GET"])
def population_health_readiness_api():
    return population_health_readiness_report()
