from flask import current_app

from app.runtime.deployment_profile import current_profile, profile_settings
from app.runtime.environment import Environment
from app.runtime.feature_flags import FeatureFlags


class RuntimeConfig:
    @staticmethod
    def load(app=None):
        app = app or current_app._get_current_object()
        profile = current_profile()
        settings = profile_settings(profile)
        return {
            "profile": profile,
            "settings": settings,
            "environment": Environment.summary(),
            "feature_flags": FeatureFlags.all(),
            "app_name": app.config.get("APP_NAME", "DxCon"),
            "database_uri_prefix": (app.config.get("SQLALCHEMY_DATABASE_URI") or "").split(":", 1)[0],
        }

    @staticmethod
    def validate(app=None):
        app = app or current_app._get_current_object()
        config = RuntimeConfig.load(app)
        issues = []
        if config["profile"] == "production" and config["settings"].get("debug"):
            issues.append("debug must be disabled in production")
        if config["profile"] == "production" and not app.config.get("SECRET_KEY"):
            issues.append("SECRET_KEY missing")
        return {"valid": not issues, "issues": issues, "config": config}
