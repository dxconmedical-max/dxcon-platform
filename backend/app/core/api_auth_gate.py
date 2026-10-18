"""Production API auth gate — deny anonymous access to high-risk prefixes.

Does not modify frozen web auth. Enforced in strict environments (staging/production)
unless TESTING is set. Accepts JWT Bearer or Flask session user_id (dual-auth workspaces).
"""

from __future__ import annotations

from flask import request, session
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.core.errors import build_error_response
from app.infrastructure.production_readiness import is_strict_env

# Exact public paths (auth not required).
PUBLIC_EXACT = frozenset(
    {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/auth/refresh",
        "/api/v1/system/health",
        "/api/v1/system/live",
        "/api/v1/system/liveness",
        "/api/v1/system/ready",
        "/api/v1/system/readiness",
        "/api/v1/system/version",
        "/api/v1/system/build",
        "/api/v1/api-platform/health",
        "/live",
        "/ready",
        # P0-6: intentionally public writes / catalog
        "/api/v1/payments/webhook",
        "/api/v1/marketplace/search",
        "/api/v1/marketplace/v2/health",
        "/api/v1/marketplace/v2/payments/webhook",
    }
)

# Prefixes that remain public (verification QR, catalogs, service ingest gaps).
PUBLIC_PREFIXES = (
    "/api/v1/reporting/verify/",
    "/results/verify/",
    "/api/v1/marketplace/catalog/",
    # SERVICE_AUTH_REQUIRED — no inbound service-credential verifier exists yet.
    # Left public rather than inventing an insecure substitute; see P0-6 report.
    "/api/v1/integrations/lis/",
    "/api/v1/integrations/his/",
)

# High-risk API prefixes that must not be anonymous in strict env.
PROTECTED_PREFIXES = (
    "/api/v1/files",
    "/api/v1/seeds",
    "/api/v1/pilot-toolkit",
    "/api/v1/security",
    "/api/v1/security-compliance",
    "/api/v1/patients",
    "/api/v1/orders",
    "/api/v1/billing",
    "/api/v1/results",
    "/api/v1/partners",
    "/api/v1/collector",
    "/api/v1/shipments",
    "/api/v1/logistics-v2",
    "/api/v1/dashboard",
    "/api/v1/mobile",
    "/api/v1/admin",
    # P0-A: highest-risk portal / clinical surfaces
    "/api/v1/clinic",
    "/api/v1/doctor",
    "/api/v1/patient",
    "/api/v1/lab",
    "/api/v1/order-lifecycle",
    "/api/v1/system/routes",
    "/api/v1/system/stats",
    "/api/v1/system/diagnostics",
    # P0-6: remaining human-operated write surfaces (device ingest is NOT listed)
    "/api/v1/marketplace",
    "/api/v1/payments",
    "/api/v1/federation",
    "/api/v1/integrations",
    "/api/v1/integration",
    "/api/v1/reception",
    "/api/v1/sample-collections",
    "/api/v1/workflow",
    "/api/v1/home-collections",
    "/api/v1/collector-operations",
    "/api/v1/scheduling",
    "/api/v1/order-execution",
    "/api/v1/mdm",
    "/api/v1/partner",
    "/api/v1/partner-portal",
    "/api/v1/logistics",
    "/api/v1/tenants",
    "/api/v1/licenses",
    "/api/v1/audit",
    "/api/v1/notification-legacy",
    "/api/v1/notification-templates",
    "/api/v1/notifications",
    "/api/v1/reports",
    "/api/v1/reporting",
    "/api/v1/ai-platform",
    "/api/v1/portal",
    "/api/v1/executive-platform",
    "/api/v1/operations-center",
    "/api/v1/pilot-readiness",
    "/api/v1/role-dashboards",
    "/api/v1/companies",
    "/api/v1/laboratories",
    "/api/v1/invoices",
    "/api/v1/contracts",
    "/api/v1/contract-prices",
    "/api/v1/order-items",
    "/api/v1/test-catalogs",
    "/api/v1/test-results",
    "/api/v1/sample-trackings",
    "/api/v1/transport-boxes",
    "/api/v1/incidents",
    "/api/v1/alerts",
    "/api/v1/ai-clinical",
    "/api/v1/api-keys",
    "/api/v1/api-clients",
    "/api/v1/api-usage",
    "/api/v1/plugins",
    "/api/v1/connectors",
    "/api/v1/webhooks",
    "/api/v1/events",
    "/api/v1/integration-queue",
    "/api/v1/crm",
    "/api/v1/operations",
    "/api/v1/knowledge",
    "/api/v1/guidelines",
    "/api/v1/biomarkers",
    "/api/v1/diseases",
    "/api/v1/correlations",
    "/api/v1/templates",
    "/api/v1/hub",
)


def _is_public(path: str) -> bool:
    if path in PUBLIC_EXACT:
        return True
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def _is_protected(path: str) -> bool:
    for prefix in PROTECTED_PREFIXES:
        if path == prefix or path.startswith(prefix + "/") or path.startswith(prefix + "?"):
            return True
        # prefix without trailing segment match for exact blueprint roots
        if path.startswith(prefix):
            return True
    return False


def _authenticated() -> bool:
    if session.get("user_id"):
        return True
    try:
        verify_jwt_in_request(optional=True)
    except Exception:
        return False
    return bool(get_jwt_identity())


def init_api_auth_gate(app):
    @app.before_request
    def enforce_api_auth_gate():
        if app.config.get("TESTING"):
            return None
        if not app.config.get("API_AUTH_GATE_ENABLED", True):
            return None
        if not is_strict_env(app):
            return None

        if request.method == "OPTIONS":
            return None

        path = request.path or ""
        if not path.startswith("/api/"):
            return None
        if _is_public(path):
            return None
        if not _is_protected(path):
            return None
        if _authenticated():
            return None

        return build_error_response(
            "UNAUTHORIZED",
            "Authorization required",
            401,
        )
