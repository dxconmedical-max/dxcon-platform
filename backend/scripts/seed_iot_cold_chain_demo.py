import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.extensions.db import db
from app.services.iot_cold_chain_service import (
    GPSMonitoringService,
    IoTDeviceService,
    TemperatureMonitoringService,
)


def seed_iot_cold_chain_demo():
    if IoTDeviceService.list_devices()["count"] > 0:
        device = IoTDeviceService.list_devices()["devices"][0]
        return {"device_id": device["id"], "already_seeded": True}

    registered = IoTDeviceService.register_device(
        {
            "device_code": "IOT-COLD-001",
            "box_code": "BOX-001",
            "device_type": "COLD_BOX",
            "serial_number": "SN-COLD-001",
            "min_temp_c": 2.0,
            "max_temp_c": 8.0,
        }
    )
    device_id = registered["device"]["id"]

    TemperatureMonitoringService.record_temperature({"device_id": device_id, "celsius": 5.5})
    TemperatureMonitoringService.record_humidity({"device_id": device_id, "humidity_percent": 45.0})
    GPSMonitoringService.record_gps(
        {"device_id": device_id, "latitude": 21.0285, "longitude": 105.8542}
    )
    GPSMonitoringService.record_shock({"device_id": device_id, "g_force": 1.2})

    alert_demo = TemperatureMonitoringService.record_temperature({"device_id": device_id, "celsius": 10.5})
    return {
        "device_id": device_id,
        "alert_created": bool(alert_demo.get("alert")),
    }


def main():
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_iot_cold_chain_demo()
        print("\n=== DXCON IOT COLD CHAIN DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
