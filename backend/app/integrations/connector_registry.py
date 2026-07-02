import json
import uuid

from app.extensions.db import db
from app.integrations.adapter_manager import AdapterManager
from app.integrations.adapter_registry import AdapterRegistry
from app.integrations.models import IntegrationConnector
from app.integrations.audit_trail import IntegrationAuditTrail


class ConnectorRegistry:
    @staticmethod
    def ensure_defaults():
        AdapterManager.initialize()
        if IntegrationConnector.query.first():
            return {"seeded": False}
        defaults = [
            ("CONN-HIS", "HIS Connector", "HIS"),
            ("CONN-LIS", "LIS Connector", "LIS"),
            ("CONN-PAYMENT", "Payment Connector", "PAYMENT"),
        ]
        for code, name, adapter_type in defaults:
            if adapter_type not in AdapterRegistry.list_types():
                continue
            db.session.add(
                IntegrationConnector(
                    connector_code=code,
                    name=name,
                    adapter_type=adapter_type,
                    config_json=json.dumps({"mode": "sandbox"}),
                    status="ACTIVE",
                )
            )
        db.session.commit()
        return {"seeded": True}

    @staticmethod
    def list_connectors():
        ConnectorRegistry.ensure_defaults()
        rows = IntegrationConnector.query.order_by(IntegrationConnector.created_at.desc()).all()
        return {"count": len(rows), "connectors": [row.to_dict() for row in rows]}

    @staticmethod
    def register(data):
        AdapterManager.initialize()
        adapter_type = (data.get("adapter_type") or "").upper()
        if adapter_type not in AdapterRegistry.list_types():
            raise ValueError(f"Unknown adapter_type: {adapter_type}")
        connector = IntegrationConnector(
            connector_code=data.get("connector_code") or f"CONN-{uuid.uuid4().hex[:8].upper()}",
            name=data.get("name") or adapter_type,
            adapter_type=adapter_type,
            config_json=json.dumps(data.get("config") or {}),
            status=data.get("status") or "ACTIVE",
        )
        db.session.add(connector)
        db.session.commit()
        IntegrationAuditTrail.write(
            action="CONNECTOR_REGISTERED",
            resource_type="IntegrationConnector",
            resource_id=connector.id,
            detail={"connector_code": connector.connector_code, "adapter_type": adapter_type},
        )
        return connector.to_dict()

    @staticmethod
    def get(connector_id):
        row = IntegrationConnector.query.filter_by(id=connector_id).first()
        if row is None:
            raise KeyError("Connector not found")
        return row.to_dict()
