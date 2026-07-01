from app.core.deployment import deployment_readiness
from app.infrastructure.production_readiness import evaluate_go_live_blockers
from app.infrastructure.runtime_validation import RuntimeValidationService
from app.runtime.runtime_config import RuntimeConfig


class InfrastructureHealthService:
    @staticmethod
    def status(app):
        runtime = RuntimeValidationService.validate_all(app)
        config = RuntimeConfig.load(app)
        deployment = deployment_readiness(app)
        return {
            "status": runtime["status"],
            "runtime_profile": config["profile"],
            "environment": config["environment"],
            "deployment_score": deployment["score"],
            "components": runtime["checks"],
            "ready_for_production": deployment["ready_for_production"],
        }


class InfrastructureReadinessService:
    @staticmethod
    def readiness(app):
        runtime = RuntimeValidationService.validate_all(app)
        config_validation = RuntimeValidationService.validate_runtime_config(app)
        deployment = deployment_readiness(app)
        blockers = evaluate_go_live_blockers(app)
        ready = (
            runtime["status"] != "DOWN"
            and config_validation["valid"]
            and deployment["ready_for_production"]
            and blockers["ready"]
        )
        return {
            "ready": ready,
            "runtime_status": runtime["status"],
            "config_valid": config_validation["valid"],
            "deployment": deployment,
            "go_live_blockers": blockers,
            "issues": config_validation.get("issues", []),
        }

    @staticmethod
    def config(app):
        payload = RuntimeConfig.load(app)
        payload["validation"] = RuntimeValidationService.validate_runtime_config(app)
        return payload
