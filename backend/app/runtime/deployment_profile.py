import os

PROFILES = ("development", "staging", "production", "testing")


def current_profile():
    env = (os.getenv("APP_ENV") or os.getenv("DXCON_ENV") or "development").lower()
    if env in PROFILES:
        return env
    if env in {"prod", "live"}:
        return "production"
    if env in {"stage", "uat"}:
        return "staging"
    if env in {"test", "ci"}:
        return "testing"
    return "development"


def profile_settings(profile=None):
    profile = profile or current_profile()
    base = {
        "profile": profile,
        "debug": profile == "development",
        "testing": profile == "testing",
        "strict_validation": profile in {"production", "staging"},
        "expose_debug_routes": profile == "development",
        "maintenance_allowed": profile != "production",
    }
    overrides = {
        "development": {"log_level": "DEBUG", "rate_limit_enabled": False},
        "staging": {"log_level": "INFO", "rate_limit_enabled": True},
        "production": {"log_level": "INFO", "rate_limit_enabled": True},
        "testing": {"log_level": "WARNING", "rate_limit_enabled": False},
    }
    base.update(overrides.get(profile, {}))
    return base
