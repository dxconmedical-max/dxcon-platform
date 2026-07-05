"""Marketplace Platform business logic for Phase 7.2."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.diagnostic_service import DiagnosticService
from app.models.marketplace_booking import MarketplaceBooking
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.plugins.plugin_manager import PluginManager
from app.plugins.plugin_registry import PluginRegistry
from app.services.integration_platform_service import SandboxService
from app.services.reporting_service import _safe

MARKETPLACE_PLATFORM_ROLES = ("SUPER_ADMIN", "ADMIN")

FEATURES = (
    "Marketplace",
    "Plugin Registry",
    "Plugin Manifest",
    "Plugin Installer",
    "Plugin Version",
    "Plugin Dependency",
    "Plugin Permission",
    "Plugin Sandbox",
    "Plugin Health",
)

PLUGIN_PERMISSIONS: dict[str, list[str]] = {
    "webhook-delivery": ["webhook:write", "webhook:read", "event:deliver"],
    "event-bridge": ["event:read", "event:write", "integration:admin"],
    "adapter-sync": ["adapter:read", "adapter:write", "queue:write"],
}

SANDBOX_SAMPLE_CONFIG: dict[str, dict] = {
    "webhook-delivery": {"endpoint_url": "https://sandbox.example/webhook", "secret": "sandbox-secret"},
    "event-bridge": {"target_system": "sandbox-crm", "batch_size": 10},
    "adapter-sync": {"poll_interval_seconds": 60, "adapter_id": "LIS"},
}


class MarketplacePlatformError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_marketplace_platform() -> dict[str, Any]:
    PluginManager.ensure_defaults()
    return {"ready": True}


def marketplace_overview() -> dict[str, Any]:
    ensure_marketplace_platform()
    services = _safe(lambda: DiagnosticService.query.filter_by(is_active=True).count(), 0)
    partners = _safe(
        lambda: Partner.query.filter(Partner.status.in_(("ACTIVE", "APPROVED"))).count(),
        0,
    )
    mappings = _safe(lambda: PartnerServiceMapping.query.count(), 0)
    bookings = _safe(lambda: MarketplaceBooking.query.count(), 0)
    return {
        "report": "marketplace_overview",
        "read_only": True,
        "active_services": services,
        "active_partners": partners,
        "service_mappings": mappings,
        "bookings_total": bookings,
        "legacy_routes": ["/marketplace", "/api/v1/marketplace/search"],
    }


def plugin_registry() -> dict[str, Any]:
    ensure_marketplace_platform()
    manifests = PluginRegistry.list_manifests()
    plugins = PluginManager.list_plugins()
    return {
        "report": "plugin_registry",
        "read_only": True,
        "registry_count": len(manifests),
        "installed_count": plugins.get("count", 0),
        "manifests": manifests,
        "plugins": plugins.get("plugins", []),
    }


def plugin_manifests() -> dict[str, Any]:
    ensure_marketplace_platform()
    items = []
    for manifest_dict in PluginRegistry.list_manifests():
        manifest = PluginRegistry.get_manifest(manifest_dict["plugin_id"])
        if manifest is None:
            continue
        items.append(manifest.to_dict())
    return {
        "report": "plugin_manifest",
        "read_only": True,
        "count": len(items),
        "manifests": items,
    }


def plugin_manifest_detail(plugin_id: str) -> dict[str, Any]:
    ensure_marketplace_platform()
    manifest = PluginRegistry.get_manifest(plugin_id)
    if manifest is None:
        raise MarketplacePlatformError(f"Unknown plugin: {plugin_id}", 404)
    return {
        "report": "plugin_manifest_detail",
        "read_only": True,
        "manifest": manifest.to_dict(),
    }


def plugin_installer() -> dict[str, Any]:
    ensure_marketplace_platform()
    plugins = PluginManager.list_plugins()
    installs = []
    for item in plugins.get("plugins", []):
        installs.append(
            {
                "plugin_id": item["plugin_id"],
                "name": item["name"],
                "version": item["version"],
                "installed": True,
                "enabled": item.get("enabled", False),
                "status": item.get("status"),
                "install_action": "PluginManager.ensure_defaults()",
                "enable_action": f"POST /api/v1/plugins/{item['plugin_id']}/enable",
            }
        )
    return {
        "report": "plugin_installer",
        "read_only": False,
        "count": len(installs),
        "installs": installs,
    }


def plugin_versions() -> dict[str, Any]:
    ensure_marketplace_platform()
    versions = []
    for item in PluginManager.list_plugins().get("plugins", []):
        versions.append(
            {
                "plugin_id": item["plugin_id"],
                "name": item["name"],
                "version": item["version"],
                "status": item.get("status"),
                "semver": item["version"],
            }
        )
    return {
        "report": "plugin_version",
        "read_only": True,
        "count": len(versions),
        "versions": versions,
    }


def plugin_dependencies() -> dict[str, Any]:
    ensure_marketplace_platform()
    graph = []
    for manifest_dict in PluginRegistry.list_manifests():
        manifest = PluginRegistry.get_manifest(manifest_dict["plugin_id"])
        if manifest is None:
            continue
        graph.append(
            {
                "plugin_id": manifest.plugin_id,
                "version": manifest.version,
                "dependencies": list(manifest.dependencies),
                "dependency_count": len(manifest.dependencies),
            }
        )
    return {
        "report": "plugin_dependency",
        "read_only": True,
        "count": len(graph),
        "dependencies": graph,
    }


def plugin_permissions() -> dict[str, Any]:
    ensure_marketplace_platform()
    rows = []
    for manifest_dict in PluginRegistry.list_manifests():
        plugin_id = manifest_dict["plugin_id"]
        perms = PLUGIN_PERMISSIONS.get(plugin_id, ["plugin:read"])
        rows.append(
            {
                "plugin_id": plugin_id,
                "name": manifest_dict.get("name"),
                "permissions": perms,
                "permission_count": len(perms),
            }
        )
    return {
        "report": "plugin_permission",
        "read_only": True,
        "count": len(rows),
        "permissions": rows,
    }


def plugin_sandbox(plugin_id: str | None = None) -> dict[str, Any]:
    ensure_marketplace_platform()
    sandbox_status = SandboxService.status()
    results = []
    plugin_ids = [plugin_id] if plugin_id else [m["plugin_id"] for m in PluginRegistry.list_manifests()]
    for pid in plugin_ids:
        if PluginRegistry.get_manifest(pid) is None:
            continue
        sample = SANDBOX_SAMPLE_CONFIG.get(pid, {})
        validation = PluginManager.validate_config(pid, sample)
        results.append(
            {
                "plugin_id": pid,
                "sample_config": sample,
                "validation": validation,
                "sandbox_ok": validation.get("valid", False),
            }
        )
    return {
        "report": "plugin_sandbox",
        "read_only": True,
        "sandbox_status": sandbox_status,
        "tests_run": len(results),
        "results": results,
    }


def plugin_health() -> dict[str, Any]:
    ensure_marketplace_platform()
    checks = []
    for item in PluginManager.list_plugins().get("plugins", []):
        plugin_id = item["plugin_id"]
        try:
            health = PluginManager.health_check(plugin_id)
            ok = health.get("status") in ("OK", "DISABLED")
        except Exception as exc:
            health = {"status": "ERROR", "error": str(exc)}
            ok = False
        checks.append(
            {
                "plugin_id": plugin_id,
                "name": item["name"],
                "enabled": item.get("enabled", False),
                "health": health,
                "ok": ok,
            }
        )
    passed = sum(1 for row in checks if row["ok"])
    return {
        "report": "plugin_health",
        "read_only": True,
        "checks_total": len(checks),
        "checks_passed": passed,
        "checks": checks,
        "overall_status": "OK" if passed == len(checks) else "DEGRADED",
    }


def marketplace_platform_dashboard() -> dict[str, Any]:
    ensure_marketplace_platform()
    marketplace = marketplace_overview()
    registry = plugin_registry()
    health = plugin_health()
    return {
        "report": "marketplace_platform_dashboard",
        "read_only": True,
        "status": health.get("overall_status", "OK"),
        "active_services": marketplace.get("active_services", 0),
        "bookings_total": marketplace.get("bookings_total", 0),
        "plugins_registered": registry.get("registry_count", 0),
        "plugins_installed": registry.get("installed_count", 0),
        "plugin_health_passed": health.get("checks_passed", 0),
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_marketplace_platform()
    dash = marketplace_platform_dashboard()
    return {
        "platform": "Marketplace Platform",
        "phase": "7.2",
        "sprint": "Marketplace",
        "status": dash["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "active_services": dash["active_services"],
            "bookings_total": dash["bookings_total"],
            "plugins_registered": dash["plugins_registered"],
            "plugins_installed": dash["plugins_installed"],
            "plugin_health_passed": dash["plugin_health_passed"],
        },
        "features": list(FEATURES),
    }


def marketplace_platform_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "7.2",
        "sprint": "Marketplace",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "marketplace": marketplace_overview(),
            "plugin_registry": plugin_registry(),
            "plugin_manifest": plugin_manifests(),
            "plugin_installer": plugin_installer(),
            "plugin_version": plugin_versions(),
            "plugin_dependency": plugin_dependencies(),
            "plugin_permission": plugin_permissions(),
            "plugin_sandbox": plugin_sandbox(),
            "plugin_health": plugin_health(),
        },
        "legacy_routes": [
            "/marketplace",
            "/api/v1/marketplace/search",
            "/api/v1/plugins",
        ],
        "sdk_guide": "docs/PLUGIN_SDK_GUIDE.md",
    }
