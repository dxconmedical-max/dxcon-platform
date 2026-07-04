from typing import Any, Dict

from app.iot.base_adapter import BaseIoTDeviceAdapter


class GenericColdChainAdapter(BaseIoTDeviceAdapter):
    adapter_type = "GENERIC"
    vendor_label = "Generic Cold Chain"


class DemoSensorAdapter(BaseIoTDeviceAdapter):
    adapter_type = "DEMO_SENSOR"
    vendor_label = "Demo Sensor Gateway"

    def normalize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        device_id = payload.get("device_id") or payload.get("deviceId")
        event_type = (payload.get("event_type") or payload.get("type") or "TEMPERATURE").upper()
        data = dict(payload)
        data["device_id"] = device_id
        if payload.get("tempC") is not None:
            data["celsius"] = payload.get("tempC")
        if payload.get("lat") is not None:
            data["latitude"] = payload.get("lat")
        if payload.get("lng") is not None:
            data["longitude"] = payload.get("lng")
        if payload.get("gForce") is not None:
            data["g_force"] = payload.get("gForce")
        return {"event_type": event_type, "device_id": device_id, "data": data}


class VendorGatewayAdapter(BaseIoTDeviceAdapter):
    adapter_type = "VENDOR_GATEWAY"
    vendor_label = "Vendor Gateway API"

    def normalize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        readings = payload.get("readings") or {}
        device_id = payload.get("device_id") or payload.get("serial")
        event_type = (payload.get("event_type") or "TELEMETRY").upper()
        data = {
            "device_id": device_id,
            "celsius": readings.get("temperature"),
            "latitude": readings.get("latitude"),
            "longitude": readings.get("longitude"),
            "g_force": readings.get("shock"),
            "battery_percent": readings.get("battery"),
        }
        return {"event_type": event_type, "device_id": device_id, "data": data}


ADAPTER_CLASSES = {
    "GENERIC": GenericColdChainAdapter,
    "DEMO_SENSOR": DemoSensorAdapter,
    "VENDOR_GATEWAY": VendorGatewayAdapter,
}
