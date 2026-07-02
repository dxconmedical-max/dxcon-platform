from app.integrations.adapter_manager import AdapterManager
from app.integrations.connector_registry import ConnectorRegistry
from app.integrations.models import IntegrationConnector


class ConnectorHealthService:
    @staticmethod
    def check(connector_id):
        row = IntegrationConnector.query.filter_by(id=connector_id).first()
        if row is None:
            raise KeyError("Connector not found")
        AdapterManager.initialize()
        try:
            AdapterManager.connect(row.adapter_type)
            health = AdapterManager.health_check(row.adapter_type)
            ok = bool(health.get("ok", True))
        except Exception as exc:
            ok = False
            health = {"ok": False, "error": str(exc)}
        return {
            "connector_id": connector_id,
            "connector_code": row.connector_code,
            "adapter_type": row.adapter_type,
            "healthy": ok,
            "details": health,
        }

    @staticmethod
    def check_all():
        ConnectorRegistry.ensure_defaults()
        results = []
        for row in IntegrationConnector.query.all():
            try:
                results.append(ConnectorHealthService.check(row.id))
            except KeyError:
                continue
        healthy = sum(1 for item in results if item.get("healthy"))
        return {"count": len(results), "healthy": healthy, "connectors": results}
