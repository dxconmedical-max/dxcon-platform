"""Connector adapter interface and implementations — Epic 3.5."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ConnectorAdapter(ABC):
  adapter_name: str = "base"
  production_ready: bool = False

  def __init__(self, connector: dict[str, Any]):
    self.connector = connector

  @abstractmethod
  def test_connection(self) -> dict[str, Any]:
    ...

  @abstractmethod
  def health_check(self) -> dict[str, Any]:
    ...

  def pull_orders(self) -> dict[str, Any]:
    return {"status": "NOT_IMPLEMENTED", "adapter": self.adapter_name}

  def push_orders(self, payload: dict[str, Any]) -> dict[str, Any]:
    return {"status": "NOT_IMPLEMENTED", "adapter": self.adapter_name}

  def pull_results(self) -> dict[str, Any]:
    return {"status": "NOT_IMPLEMENTED", "adapter": self.adapter_name}

  def push_results(self, payload: dict[str, Any]) -> dict[str, Any]:
    return {"status": "NOT_IMPLEMENTED", "adapter": self.adapter_name}

  def acknowledge_message(self, message_id: str) -> dict[str, Any]:
    return {"status": "ACKNOWLEDGED", "message_id": message_id}

  def transform_inbound(self, payload: Any) -> dict[str, Any]:
    return {"canonical": payload}

  def transform_outbound(self, payload: dict[str, Any]) -> dict[str, Any]:
    return payload


class CSVAdapter(ConnectorAdapter):
  adapter_name = "CSV"
  production_ready = True

  def test_connection(self) -> dict[str, Any]:
    return {"ok": True, "adapter": self.adapter_name, "mode": "file_upload"}

  def health_check(self) -> dict[str, Any]:
    return {"status": "OK", "adapter": self.adapter_name, "production_ready": True}

  def transform_inbound(self, payload: Any) -> dict[str, Any]:
    return {"format": "csv", "rows": payload}


class JSONAdapter(ConnectorAdapter):
  adapter_name = "JSON"
  production_ready = True

  def test_connection(self) -> dict[str, Any]:
    return {"ok": True, "adapter": self.adapter_name, "mode": "json_payload"}

  def health_check(self) -> dict[str, Any]:
    return {"status": "OK", "adapter": self.adapter_name, "production_ready": True}

  def transform_inbound(self, payload: Any) -> dict[str, Any]:
    return {"format": "json", "data": payload}


class RESTAdapter(ConnectorAdapter):
  adapter_name = "REST"
  production_ready = False

  def test_connection(self) -> dict[str, Any]:
    return {"ok": False, "adapter": self.adapter_name, "foundation_only": True}

  def health_check(self) -> dict[str, Any]:
    return {"status": "FOUNDATION", "production_ready": False}


class HL7Adapter(ConnectorAdapter):
  adapter_name = "HL7_V2"
  production_ready = False

  def test_connection(self) -> dict[str, Any]:
    return {"ok": False, "foundation_only": True, "supported": ["ADT", "ORM", "ORU"]}

  def health_check(self) -> dict[str, Any]:
    return {"status": "FOUNDATION", "production_ready": False}


class FHIRAdapter(ConnectorAdapter):
  adapter_name = "FHIR_R4"
  production_ready = False

  def test_connection(self) -> dict[str, Any]:
    return {"ok": False, "foundation_only": True}

  def health_check(self) -> dict[str, Any]:
    return {"status": "FOUNDATION", "production_ready": False}


class SFTPAdapter(ConnectorAdapter):
  adapter_name = "SFTP"
  production_ready = False

  def test_connection(self) -> dict[str, Any]:
    return {"ok": False, "foundation_only": True}

  def health_check(self) -> dict[str, Any]:
    return {"status": "FOUNDATION", "production_ready": False}


class WebhookAdapter(ConnectorAdapter):
  adapter_name = "WEBHOOK"
  production_ready = True

  def test_connection(self) -> dict[str, Any]:
    return {"ok": True, "adapter": self.adapter_name}

  def health_check(self) -> dict[str, Any]:
    return {"status": "OK", "production_ready": True}


class ManualAdapter(ConnectorAdapter):
  adapter_name = "MANUAL"
  production_ready = True

  def test_connection(self) -> dict[str, Any]:
    return {"ok": True, "adapter": self.adapter_name}

  def health_check(self) -> dict[str, Any]:
    return {"status": "OK", "production_ready": True}


ADAPTER_REGISTRY: dict[str, type[ConnectorAdapter]] = {
  "CSV": CSVAdapter,
  "JSON": JSONAdapter,
  "REST": RESTAdapter,
  "HL7_V2": HL7Adapter,
  "FHIR_R4": FHIRAdapter,
  "SFTP": SFTPAdapter,
  "WEBHOOK": WebhookAdapter,
  "MANUAL": ManualAdapter,
}


def get_adapter(protocol: str, connector: dict[str, Any]) -> ConnectorAdapter:
  cls = ADAPTER_REGISTRY.get(protocol.upper(), ManualAdapter)
  return cls(connector)
