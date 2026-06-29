from datetime import datetime

from app.core.statuses import (
    COLD_BOX_ACTIVE,
    COLD_CHAIN_ALERT_BATTERY_LOW,
    COLD_CHAIN_ALERT_OPEN,
    COLD_CHAIN_ALERT_SHOCK,
    COLD_CHAIN_ALERT_TEMP_HIGH,
    COLD_CHAIN_ALERT_TEMP_LOW,
    IOT_DEVICE_ACTIVE,
)
from app.extensions.db import db
from app.models.battery_event import BatteryEvent
from app.models.cold_box_device import ColdBoxDevice
from app.models.cold_chain_alert import ColdChainAlert
from app.models.gps_reading import GPSReading
from app.models.humidity_reading import HumidityReading
from app.models.iot_device import IoTDevice
from app.models.shock_event import ShockEvent
from app.models.temperature_reading import TemperatureReading


class IoTError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class IoTDeviceService:

    @staticmethod
    def _get_device_or_raise(device_id):
        device = IoTDevice.query.get(device_id)
        if not device:
            raise IoTError("IoT device not found", 404)
        return device

    @staticmethod
    def list_devices(status=None, device_type=None):
        query = IoTDevice.query
        if status:
            query = query.filter_by(status=status)
        if device_type:
            query = query.filter_by(device_type=device_type)
        rows = query.order_by(IoTDevice.created_at.desc()).all()
        payload = []
        for row in rows:
            item = row.to_dict()
            cold_box = ColdBoxDevice.query.filter_by(device_id=row.id).first()
            item["cold_box"] = cold_box.to_dict() if cold_box else None
            payload.append(item)
        return {"count": len(payload), "devices": payload}

    @staticmethod
    def register_device(data):
        device = IoTDevice(
            device_code=data.get("device_code") or f"IOT-{IoTDevice.query.count() + 1:04d}",
            device_type=data.get("device_type", "COLD_BOX"),
            serial_number=data.get("serial_number"),
            partner_id=data.get("partner_id"),
            status=data.get("status", IOT_DEVICE_ACTIVE),
            last_seen_at=datetime.utcnow(),
        )
        db.session.add(device)
        db.session.flush()

        cold_box = None
        if device.device_type == "COLD_BOX":
            cold_box = ColdBoxDevice(
                device_id=device.id,
                box_code=data.get("box_code") or f"BOX-{ColdBoxDevice.query.count() + 1:04d}",
                capacity_liters=data.get("capacity_liters", 20),
                min_temp_c=data.get("min_temp_c", 2.0),
                max_temp_c=data.get("max_temp_c", 8.0),
                status=COLD_BOX_ACTIVE,
            )
            db.session.add(cold_box)

        db.session.commit()
        return {"device": device.to_dict(), "cold_box": cold_box.to_dict() if cold_box else None}


class ColdChainAlertService:

    @staticmethod
    def _generate_code():
        return f"CCA-{ColdChainAlert.query.count() + 1:06d}"

    @staticmethod
    def create_alert(device_id, alert_type, message, severity="HIGH"):
        alert = ColdChainAlert(
            device_id=device_id,
            alert_code=ColdChainAlertService._generate_code(),
            alert_type=alert_type,
            severity=severity,
            message=message,
            status=COLD_CHAIN_ALERT_OPEN,
        )
        db.session.add(alert)
        db.session.flush()
        return alert

    @staticmethod
    def list_alerts(device_id=None, status=None):
        query = ColdChainAlert.query
        if device_id:
            query = query.filter_by(device_id=device_id)
        if status:
            query = query.filter_by(status=status)
        rows = query.order_by(ColdChainAlert.created_at.desc()).all()
        return {"count": len(rows), "alerts": [row.to_dict() for row in rows]}


class TemperatureMonitoringService:

    @staticmethod
    def record_temperature(data):
        device_id = data.get("device_id")
        celsius = data.get("celsius")
        if device_id is None or celsius is None:
            raise IoTError("device_id and celsius are required", 400)

        device = IoTDeviceService._get_device_or_raise(device_id)
        cold_box = ColdBoxDevice.query.filter_by(device_id=device_id).first()
        reading = TemperatureReading(
            device_id=device_id,
            cold_box_id=cold_box.id if cold_box else None,
            celsius=float(celsius),
            recorded_at=datetime.utcnow(),
        )
        db.session.add(reading)
        device.last_seen_at = datetime.utcnow()

        alert = None
        if cold_box:
            if celsius > cold_box.max_temp_c:
                alert = ColdChainAlertService.create_alert(
                    device_id,
                    COLD_CHAIN_ALERT_TEMP_HIGH,
                    f"Temperature {celsius}C exceeds max {cold_box.max_temp_c}C",
                )
            elif celsius < cold_box.min_temp_c:
                alert = ColdChainAlertService.create_alert(
                    device_id,
                    COLD_CHAIN_ALERT_TEMP_LOW,
                    f"Temperature {celsius}C below min {cold_box.min_temp_c}C",
                )

        db.session.commit()
        payload = {"reading": reading.to_dict()}
        if alert:
            payload["alert"] = alert.to_dict()
        return payload

    @staticmethod
    def record_humidity(data):
        device_id = data.get("device_id")
        humidity_percent = data.get("humidity_percent")
        if device_id is None or humidity_percent is None:
            raise IoTError("device_id and humidity_percent are required", 400)

        device = IoTDeviceService._get_device_or_raise(device_id)
        reading = HumidityReading(
            device_id=device_id,
            humidity_percent=float(humidity_percent),
            recorded_at=datetime.utcnow(),
        )
        db.session.add(reading)
        device.last_seen_at = datetime.utcnow()
        db.session.commit()
        return {"reading": reading.to_dict()}


class GPSMonitoringService:

    @staticmethod
    def record_gps(data):
        device_id = data.get("device_id")
        latitude = data.get("latitude")
        longitude = data.get("longitude")
        if device_id is None or latitude is None or longitude is None:
            raise IoTError("device_id, latitude, and longitude are required", 400)

        device = IoTDeviceService._get_device_or_raise(device_id)
        reading = GPSReading(
            device_id=device_id,
            latitude=float(latitude),
            longitude=float(longitude),
            recorded_at=datetime.utcnow(),
        )
        db.session.add(reading)
        device.last_seen_at = datetime.utcnow()
        db.session.commit()
        return {"reading": reading.to_dict()}

    @staticmethod
    def record_shock(data):
        device_id = data.get("device_id")
        g_force = data.get("g_force")
        if device_id is None or g_force is None:
            raise IoTError("device_id and g_force are required", 400)

        device = IoTDeviceService._get_device_or_raise(device_id)
        event = ShockEvent(
            device_id=device_id,
            g_force=float(g_force),
            recorded_at=datetime.utcnow(),
        )
        db.session.add(event)
        device.last_seen_at = datetime.utcnow()

        alert = None
        if float(g_force) >= 3.0:
            alert = ColdChainAlertService.create_alert(
                device_id,
                COLD_CHAIN_ALERT_SHOCK,
                f"Shock event detected: {g_force}g",
            )

        db.session.commit()
        payload = {"event": event.to_dict()}
        if alert:
            payload["alert"] = alert.to_dict()
        return payload

    @staticmethod
    def record_battery(data):
        device_id = data.get("device_id")
        battery_percent = data.get("battery_percent")
        if device_id is None or battery_percent is None:
            raise IoTError("device_id and battery_percent are required", 400)

        device = IoTDeviceService._get_device_or_raise(device_id)
        event = BatteryEvent(
            device_id=device_id,
            battery_percent=float(battery_percent),
            recorded_at=datetime.utcnow(),
        )
        db.session.add(event)
        device.last_seen_at = datetime.utcnow()

        alert = None
        if float(battery_percent) <= 20:
            alert = ColdChainAlertService.create_alert(
                device_id,
                COLD_CHAIN_ALERT_BATTERY_LOW,
                f"Battery low: {battery_percent}%",
                severity="MEDIUM",
            )

        db.session.commit()
        payload = {"event": event.to_dict()}
        if alert:
            payload["alert"] = alert.to_dict()
        return payload


class ColdChainService:

    @staticmethod
    def get_status(device_id=None):
        query = IoTDevice.query.filter_by(device_type="COLD_BOX", status=IOT_DEVICE_ACTIVE)
        if device_id:
            query = query.filter_by(id=device_id)
        devices = query.all()
        payload = []

        for device in devices:
            cold_box = ColdBoxDevice.query.filter_by(device_id=device.id).first()
            latest_temp = (
                TemperatureReading.query.filter_by(device_id=device.id)
                .order_by(TemperatureReading.recorded_at.desc())
                .first()
            )
            latest_gps = (
                GPSReading.query.filter_by(device_id=device.id)
                .order_by(GPSReading.recorded_at.desc())
                .first()
            )
            open_alerts = ColdChainAlert.query.filter_by(
                device_id=device.id,
                status=COLD_CHAIN_ALERT_OPEN,
            ).count()
            in_range = True
            if latest_temp and cold_box:
                in_range = cold_box.min_temp_c <= latest_temp.celsius <= cold_box.max_temp_c

            payload.append(
                {
                    "device": device.to_dict(),
                    "cold_box": cold_box.to_dict() if cold_box else None,
                    "latest_temperature": latest_temp.to_dict() if latest_temp else None,
                    "latest_gps": latest_gps.to_dict() if latest_gps else None,
                    "open_alerts": open_alerts,
                    "in_range": in_range,
                }
            )

        return {
            "count": len(payload),
            "devices": payload,
            "summary": {
                "devices_total": len(payload),
                "devices_in_range": len([item for item in payload if item["in_range"]]),
                "open_alerts_total": sum(item["open_alerts"] for item in payload),
            },
        }
