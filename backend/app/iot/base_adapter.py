from typing import Any, Dict


class BaseIoTDeviceAdapter:
    adapter_type = "GENERIC"
    vendor_label = "Generic IoT"

    def validate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not payload.get("device_id") and not payload.get("deviceId"):
            return {"ok": False, "message": "device_id is required"}
        return {"ok": True}

    def normalize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        device_id = payload.get("device_id") or payload.get("deviceId")
        event_type = (payload.get("event_type") or payload.get("type") or "TEMPERATURE").upper()
        return {
            "event_type": event_type,
            "device_id": device_id,
            "data": payload,
        }

    def ingest(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        validation = self.validate(payload)
        if not validation.get("ok"):
            raise ValueError(validation.get("message") or "Invalid payload")
        return self.normalize(payload)
