from flask import Blueprint, current_app

from app.infrastructure.infrastructure_services import InfrastructureHealthService, InfrastructureReadinessService
from app.infrastructure.recovery_service import RecoveryService
from app.infrastructure.scaling_advisor import ScalingAdvisor
from app.runtime.runtime_config import RuntimeConfig


deployment_infra_web_bp = Blueprint("deployment_infra_web", __name__)


def _styles():
    return """
    <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #0b1220; color: #e5e7eb; }
    .layout { display: flex; min-height: 100vh; }
    .sidebar { width: 220px; background: #111827; padding: 20px; }
    .sidebar a { color: #93c5fd; display: block; margin: 8px 0; text-decoration: none; }
    .sidebar a.active { color: #fff; font-weight: bold; }
    .content { flex: 1; padding: 24px; }
    .card { background: #111827; border: 1px solid #374151; padding: 16px; margin-bottom: 16px; border-radius: 8px; }
    </style>
    """


def _sidebar(active):
    links = [
        ("/deployment", "Overview"),
        ("/deployment/readiness", "Readiness"),
        ("/deployment/runtime", "Runtime"),
        ("/deployment/scaling", "Scaling"),
        ("/deployment/recovery", "Recovery"),
    ]
    items = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{label}</a>' for href, label in links
    )
    return f'<div class="sidebar"><h2>Deployment</h2>{items}</div>'


@deployment_infra_web_bp.route("/deployment")
def deployment_home():
    app = current_app._get_current_object()
    status = InfrastructureHealthService.status(app)
    return f"""<!DOCTYPE html><html><head><title>Deployment</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/deployment")}<div class="content">
    <h1>Deployment & Infrastructure</h1>
    <div class="card">Status: {status["status"]} | Profile: {status["runtime_profile"]} | Score: {status["deployment_score"]}</div>
    </div></div></body></html>"""


@deployment_infra_web_bp.route("/deployment/readiness")
def deployment_readiness_page():
    app = current_app._get_current_object()
    readiness = InfrastructureReadinessService.readiness(app)
    return f"""<!DOCTYPE html><html><head><title>Readiness</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/deployment/readiness")}<div class="content">
    <h1>Infrastructure Readiness</h1>
    <div class="card">Ready: {readiness["ready"]} | Runtime: {readiness["runtime_status"]}</div>
    </div></div></body></html>"""


@deployment_infra_web_bp.route("/deployment/runtime")
def deployment_runtime_page():
    config = RuntimeConfig.load(current_app._get_current_object())
    return f"""<!DOCTYPE html><html><head><title>Runtime</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/deployment/runtime")}<div class="content">
    <h1>Runtime Configuration</h1>
    <div class="card">Profile: {config["profile"]} | Provider: {config["environment"]["provider"]}</div>
    <div class="card">Feature flags: {len(config["feature_flags"])} configured</div>
    </div></div></body></html>"""


@deployment_infra_web_bp.route("/deployment/scaling")
def deployment_scaling_page():
    advice = ScalingAdvisor.recommend(current_app._get_current_object())
    return f"""<!DOCTYPE html><html><head><title>Scaling</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/deployment/scaling")}<div class="content">
    <h1>Scaling Advisor</h1>
    <div class="card">Workers: {advice["workers"]["current"]} → {advice["workers"]["recommended"]}</div>
    <div class="card">DB pool: {advice["database_pool"]["current"]} → {advice["database_pool"]["recommended"]}</div>
    </div></div></body></html>"""


@deployment_infra_web_bp.route("/deployment/recovery")
def deployment_recovery_page():
    RecoveryService.ensure_defaults()
    summary = RecoveryService.summary()
    return f"""<!DOCTYPE html><html><head><title>Recovery</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/deployment/recovery")}<div class="content">
    <h1>Disaster Recovery</h1>
    <div class="card">Plans: {summary["plans"]} | Tests: {summary["tests"]} | Reports: {summary["reports"]}</div>
    </div></div></body></html>"""
