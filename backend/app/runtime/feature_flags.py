import os


DEFAULT_FLAGS = {
    "maintenance_mode": False,
    "integration_sandbox": True,
    "notification_demo_providers": True,
    "observability_platform": True,
    "operations_platform": True,
    "strict_runtime_validation": False,
}


class FeatureFlags:
    @staticmethod
    def all():
        flags = dict(DEFAULT_FLAGS)
        prefix = "DXCON_FEATURE_"
        for key in DEFAULT_FLAGS:
            env_key = prefix + key.upper()
            if env_key in os.environ:
                flags[key] = os.getenv(env_key, "").lower() in {"1", "true", "yes", "on"}
        return flags

    @staticmethod
    def enabled(name):
        return FeatureFlags.all().get(name, False)
