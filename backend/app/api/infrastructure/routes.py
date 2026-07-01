from flask import Blueprint, current_app

from app.infrastructure.infrastructure_services import InfrastructureHealthService, InfrastructureReadinessService
from app.infrastructure.recovery_service import RecoveryService
from app.infrastructure.scaling_advisor import ScalingAdvisor


infrastructure_bp = Blueprint("infrastructure", __name__, url_prefix="/api/v1/infrastructure")


@infrastructure_bp.route("/status", methods=["GET"])
def infrastructure_status():
    app = current_app._get_current_object()
    RecoveryService.ensure_defaults()
    return InfrastructureHealthService.status(app)


@infrastructure_bp.route("/readiness", methods=["GET"])
def infrastructure_readiness():
    app = current_app._get_current_object()
    payload = InfrastructureReadinessService.readiness(app)
    status = 200 if payload["ready"] else 503
    return payload, status


@infrastructure_bp.route("/config", methods=["GET"])
def infrastructure_config():
    app = current_app._get_current_object()
    return InfrastructureReadinessService.config(app)


@infrastructure_bp.route("/scaling", methods=["GET"])
def infrastructure_scaling():
    return ScalingAdvisor.recommend(current_app._get_current_object())


@infrastructure_bp.route("/recovery", methods=["GET"])
def infrastructure_recovery():
    RecoveryService.ensure_defaults()
    return {
        "summary": RecoveryService.summary(),
        "plans": RecoveryService.list_plans(),
    }
