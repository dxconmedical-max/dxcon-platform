"""Mobile Platform backend readiness for Phase 7.4."""

from __future__ import annotations

from datetime import datetime
from typing import Any

MOBILE_PLATFORM_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "Collector API",
    "Doctor API",
    "Patient API",
    "Notification API",
    "Offline Sync API",
    "Token Refresh",
    "Conflict Resolution",
    "PWA Manifest",
)

MOBILE_ROUTES = {
    "collector_api": {"prefix": "/api/v1/collector", "ops": "/api/v1/collector-operations"},
    "doctor_api": {"prefix": "/api/v1/doctor", "web": "/doctor-portal"},
    "patient_api": {"prefix": "/api/v1/patient", "mobile": "/api/v1/mobile"},
    "notification_api": {"prefix": "/api/v1/notifications", "center": "/api/v1/notification-center"},
    "offline_sync_api": {"prefix": "/api/v1/mobile/sync", "status": "scaffold"},
    "token_refresh": {"prefix": "/api/v1/auth/refresh", "logout": "/api/v1/auth/logout"},
}


def ensure_mobile_platform() -> dict[str, Any]:
    return {"ready": True}


def _section(name: str, routes: dict) -> dict[str, Any]:
    return {"report": name, "read_only": True, "routes": routes, "status": "READY"}


def collector_api() -> dict[str, Any]:
    return _section("collector_api", MOBILE_ROUTES["collector_api"])


def doctor_api() -> dict[str, Any]:
    return _section("doctor_api", MOBILE_ROUTES["doctor_api"])


def patient_api() -> dict[str, Any]:
    return _section("patient_api", MOBILE_ROUTES["patient_api"])


def notification_api() -> dict[str, Any]:
    return _section("notification_api", MOBILE_ROUTES["notification_api"])


def offline_sync_api() -> dict[str, Any]:
    return {
        "report": "offline_sync_api",
        "strategy": "client_queue_with_server_reconciliation",
        "endpoints": ["/api/v1/mobile/sync/push", "/api/v1/mobile/sync/pull"],
        "status": "SCAFFOLD",
    }


def token_refresh() -> dict[str, Any]:
    return _section("token_refresh", MOBILE_ROUTES["token_refresh"])


def conflict_resolution() -> dict[str, Any]:
    return {
        "report": "conflict_resolution",
        "strategy": "last_write_wins_with_audit",
        "status": "SCAFFOLD",
    }


def pwa_manifest() -> dict[str, Any]:
    return {
        "report": "pwa_manifest",
        "name": "DxCon Mobile",
        "short_name": "DxCon",
        "start_url": "/collector",
        "display": "standalone",
        "theme_color": "#0a4b5c",
        "status": "READY",
    }


def dashboard_payload() -> dict[str, Any]:
    return {
        "platform": "Mobile Platform",
        "phase": "7.4",
        "sprint": "Mobile Platform",
        "status": "OK",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {"mobile_api_groups": len(FEATURES), "auth_refresh": True, "pwa_ready": True},
        "features": list(FEATURES),
    }


def mobile_platform_readiness_report() -> dict[str, Any]:
    d = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "7.4",
        "platform": d["platform"],
        "status": d["status"],
        "summary": d["summary"],
        "features": list(FEATURES),
        "sections": {
            "collector_api": collector_api(),
            "doctor_api": doctor_api(),
            "patient_api": patient_api(),
            "notification_api": notification_api(),
            "offline_sync_api": offline_sync_api(),
            "token_refresh": token_refresh(),
            "conflict_resolution": conflict_resolution(),
            "pwa_manifest": pwa_manifest(),
        },
        "legacy_routes": ["/api/v1/collector", "/api/v1/doctor", "/api/v1/patient", "/api/v1/auth/refresh"],
        "guide": "docs/MOBILE_BACKEND_GUIDE.md",
    }
