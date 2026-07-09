"""Production domain and URL configuration — Sprint 011."""

from __future__ import annotations

from urllib.parse import urlparse

from flask import current_app, request

SUPPORTED_DOMAINS = (
    "dxcon.com.vn",
    "www.dxcon.com.vn",
    "app.dxcon.com.vn",
    "admin.dxcon.com.vn",
    "doctor.dxcon.com.vn",
    "patient.dxcon.com.vn",
    "lab.dxcon.com.vn",
    "clinic.dxcon.com.vn",
    "collector.dxcon.com.vn",
    "api.dxcon.com.vn",
)

LEGACY_API_HOST = "dxcon-ap.onrender.com"


def _host_from_url(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return (parsed.hostname or "").lower()


def public_site_url() -> str:
    return (current_app.config.get("PUBLIC_SITE_URL") or "https://dxcon.com.vn").rstrip("/")


def web_app_url() -> str:
    return (current_app.config.get("WEB_APP_URL") or "https://app.dxcon.com.vn").rstrip("/")


def api_base_url() -> str:
    return (current_app.config.get("API_BASE_URL") or "https://api.dxcon.com.vn").rstrip("/")


def demo_mode_enabled() -> bool:
    return bool(current_app.config.get("DEMO_MODE"))


def is_production_env() -> bool:
    return (current_app.config.get("APP_ENV") or "development").lower() == "production"


def request_host() -> str:
    return (request.host or "").split(":")[0].lower()


def is_web_app_host() -> bool:
    host = request_host()
    web_host = _host_from_url(web_app_url())
    if not web_host:
        return host.startswith("app.")
    return host == web_host


def is_public_site_host() -> bool:
    host = request_host()
    public_host = _host_from_url(public_site_url())
    if host in ("localhost", "127.0.0.1", "testserver"):
        return False
    if public_host and host in (public_host, f"www.{public_host}"):
        return True
    return host in ("dxcon.com.vn", "www.dxcon.com.vn")


def public_entry_path() -> str:
    """Marketing hosts land on /home; app hosts land on /login."""
    if is_web_app_host():
        return "/login"
    if is_public_site_host():
        return "/home"
    return "/login"


def domain_configuration_report() -> dict:
    app = current_app._get_current_object()
    return {
        "public_site_url": app.config.get("PUBLIC_SITE_URL"),
        "web_app_url": app.config.get("WEB_APP_URL"),
        "api_base_url": app.config.get("API_BASE_URL"),
        "demo_mode": demo_mode_enabled(),
        "supported_domains": list(SUPPORTED_DOMAINS),
        "legacy_api_host": LEGACY_API_HOST,
        "cors_origins": app.config.get("CORS_ORIGINS"),
    }
