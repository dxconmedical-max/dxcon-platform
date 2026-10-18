import os
import sys
import unittest
import tempfile
import threading
import json
import hmac
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Use a temporary SQLite file so concurrency tests share the same DB.
_tmp = tempfile.NamedTemporaryFile(prefix="dxcon_p0d_iot_", suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"


class P0DIoTIngestionSecurityTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.extensions.db import db
        from app.services.iot_cold_chain_service import IoTDeviceService

        # Re-assert file DB — other modules may have overwritten DATABASE_URL at import.
        os.environ["DATABASE_URL"] = f"sqlite:///{_tmp.name}"
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()

        db.create_all()

        self.device_secret = "DXCON-IOT-INGEST-SECRET"
        self.device_a = IoTDeviceService.register_device(
            {
                "device_code": "IOT-A",
                "box_code": "BOX-A",
                "device_type": "COLD_BOX",
                "serial_number": "SN-A",
                "partner_id": "ORG-A",
                "ingest_secret": self.device_secret,
            }
        )["device"]
        self.device_b = IoTDeviceService.register_device(
            {
                "device_code": "IOT-B",
                "box_code": "BOX-B",
                "device_type": "COLD_BOX",
                "serial_number": "SN-B",
                "partner_id": "ORG-B",
                "ingest_secret": self.device_secret,
            }
        )["device"]
        self.device_disabled = IoTDeviceService.register_device(
            {
                "device_code": "IOT-DISABLED",
                "box_code": "BOX-DISABLED",
                "device_type": "COLD_BOX",
                "serial_number": "SN-DISABLED",
                "partner_id": "ORG-A",
                "status": "INACTIVE",
                "ingest_secret": self.device_secret,
            }
        )["device"]

        self.client = self.app.test_client()

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        try:
            os.remove(os.environ["DATABASE_URL"].replace("sqlite:///", "", 1))
        except Exception:
            pass

    def _headers(self, device):
        return {"X-Device-Id": device["id"], "X-Device-Secret": self.device_secret}

    def _post_ingest(self, device, payload, *, headers=None, nonce=None, event_id=None):
        p = dict(payload or {})
        if nonce is not None:
            p["nonce"] = nonce
        if event_id is not None:
            p["event_id"] = event_id
        if "device_id" not in p:
            p["device_id"] = device["id"]
        return self.client.post(
            "/api/v1/iot-logistics/ingest",
            headers=headers or self._headers(device),
            json={"adapter_type": "GENERIC", "payload": p},
        )

    def _post_ingest_raw_body(self, device, payload, *, headers, signature: str):
        body = json.dumps({"adapter_type": "GENERIC", "payload": payload}, separators=(",", ":")).encode("utf-8")
        h = dict(headers)
        h["Content-Type"] = "application/json"
        h["X-Device-Signature"] = signature
        return self.client.post("/api/v1/iot-logistics/ingest", data=body, headers=h)

    def test_missing_device_secret_is_401(self):
        resp = self.client.post(
            "/api/v1/iot-logistics/ingest",
            headers={"X-Device-Id": self.device_a["id"]},
            json={"adapter_type": "GENERIC", "payload": {"event_type": "TEMPERATURE", "device_id": self.device_a["id"], "celsius": 4.5}},
        )
        self.assertEqual(resp.status_code, 401)

    def test_invalid_device_secret_is_403(self):
        resp = self.client.post(
            "/api/v1/iot-logistics/ingest",
            headers={"X-Device-Id": self.device_a["id"], "X-Device-Secret": "wrong"},
            json={"adapter_type": "GENERIC", "payload": {"event_type": "TEMPERATURE", "device_id": self.device_a["id"], "celsius": 4.5}},
        )
        self.assertEqual(resp.status_code, 403)

    def test_disabled_device_is_403(self):
        resp = self._post_ingest(
            self.device_disabled,
            {"event_type": "TEMPERATURE", "celsius": 4.5},
            event_id="evt-disabled-1",
        )
        self.assertEqual(resp.status_code, 403)

    def test_valid_device_ingest_allowed(self):
        resp = self._post_ingest(
            self.device_a,
            {"event_type": "TEMPERATURE", "celsius": 4.5},
            event_id="evt-valid-1",
        )
        self.assertEqual(resp.status_code, 200)

    def test_spoofed_device_id_is_rejected(self):
        resp = self._post_ingest(
            self.device_a,
            {"event_type": "TEMPERATURE", "device_id": self.device_b["id"], "celsius": 4.5},
            event_id="evt-spoof-device-1",
        )
        self.assertEqual(resp.status_code, 403)

    def test_device_cannot_spoof_tenant_partner(self):
        resp = self._post_ingest(
            self.device_a,
            {
                "event_type": "TEMPERATURE",
                "celsius": 4.5,
                "partner_id": self.device_b["partner_id"],
            },
            event_id="evt-spoof-tenant-1",
        )
        self.assertEqual(resp.status_code, 403)

    def test_spoofed_organization_selector_is_rejected(self):
        resp = self._post_ingest(
            self.device_a,
            {
                "event_type": "TEMPERATURE",
                "celsius": 4.5,
                "organization_id": self.device_b["partner_id"],
            },
            event_id="evt-spoof-org-1",
        )
        self.assertEqual(resp.status_code, 403)

    def test_invalid_latitude_rejected(self):
        resp = self._post_ingest(
            self.device_a,
            {"event_type": "GPS", "latitude": 999, "longitude": 106.5},
            event_id="evt-bad-lat-1",
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_longitude_rejected(self):
        resp = self._post_ingest(
            self.device_a,
            {"event_type": "GPS", "latitude": 10.5, "longitude": 999},
            event_id="evt-bad-lon-1",
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_battery_rejected(self):
        resp = self._post_ingest(
            self.device_a,
            {"event_type": "BATTERY", "battery_percent": 150},
            event_id="evt-bad-battery-1",
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_timestamp_future_rejected(self):
        future = (datetime.now(tz=timezone.utc) + timedelta(hours=2)).isoformat()
        resp = self._post_ingest(
            self.device_a,
            {"event_type": "TEMPERATURE", "celsius": 4.5, "timestamp": future},
            event_id="evt-bad-ts-1",
        )
        self.assertEqual(resp.status_code, 400)

    def test_invalid_humidity_rejected(self):
        resp = self.client.post(
            "/api/v1/iot/readings/humidity",
            headers=self._headers(self.device_a),
            json={
                "device_id": self.device_a["id"],
                "humidity_percent": 120.0,
                "event_id": "evt-bad-hum-1",
            },
        )
        self.assertEqual(resp.status_code, 400)

    def test_duplicate_event_is_idempotent(self):
        payload = {"event_type": "TEMPERATURE", "celsius": 4.5}
        r1 = self._post_ingest(self.device_a, payload, event_id="evt-dupe-1")
        r2 = self._post_ingest(self.device_a, payload, event_id="evt-dupe-1")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        from app.models.temperature_reading import TemperatureReading

        rows = TemperatureReading.query.filter_by(device_id=self.device_a["id"]).all()
        self.assertEqual(len(rows), 1)

    def test_same_event_id_different_payload_is_conflict(self):
        r1 = self._post_ingest(self.device_a, {"event_type": "TEMPERATURE", "celsius": 4.5}, event_id="evt-conflict-1")
        r2 = self._post_ingest(self.device_a, {"event_type": "TEMPERATURE", "celsius": 5.5}, event_id="evt-conflict-1")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 409)

    def test_replayed_nonce_is_rejected(self):
        r1 = self._post_ingest(
            self.device_a,
            {"event_type": "TEMPERATURE", "celsius": 4.5},
            event_id=None,
            nonce="n1",
        )
        r2 = self._post_ingest(
            self.device_a,
            {"event_type": "TEMPERATURE", "celsius": 4.5},
            event_id=None,
            nonce="n1",
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 409)

    def test_invalid_signature_rejected(self):
        resp = self.client.post(
            "/api/v1/iot-logistics/ingest",
            headers={
                "X-Device-Id": self.device_a["id"],
                "X-Device-Secret": self.device_secret,
                "X-Device-Signature": "deadbeef",
            },
            json={
                "adapter_type": "GENERIC",
                "payload": {
                    "event_type": "TEMPERATURE",
                    "device_id": self.device_a["id"],
                    "celsius": 4.5,
                    "event_id": "evt-bad-sig-1",
                },
            },
        )
        self.assertEqual(resp.status_code, 403)

    def test_human_session_cannot_impersonate_device(self):
        from app.models.user import User
        from app.core.passwords import hash_password
        from app.extensions.db import db

        user = User(email="human@demo.dxcon.test", role="ADMIN", password_hash=hash_password("pw"), is_active=True)
        db.session.add(user)
        db.session.commit()
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

        resp = self.client.post(
            "/api/v1/iot-logistics/ingest",
            json={"adapter_type": "GENERIC", "payload": {"event_type": "TEMPERATURE", "device_id": self.device_a["id"], "celsius": 4.5}},
        )
        self.assertEqual(resp.status_code, 401)

    def test_audit_actor_is_device_derived(self):
        # Ensure actor stored in custody is device-derived (not session email).
        r = self._post_ingest(
            self.device_a,
            {"event_type": "TEMPERATURE", "celsius": 4.5},
            event_id="evt-audit-1",
        )
        self.assertEqual(r.status_code, 200)

        from app.models.logistics_tracking import ChainOfCustodyEvent

        event = (
            ChainOfCustodyEvent.query.filter_by(reference_type="IoTDevice", reference_id=self.device_a["id"])
            .order_by(ChainOfCustodyEvent.created_at.desc())
            .first()
        )
        self.assertIsNotNone(event)
        self.assertEqual(event.actor, f"device:{self.device_a['device_code']}")

    def test_missing_event_id_and_nonce_rejected_for_ingest(self):
        resp = self._post_ingest(
            self.device_a,
            {"event_type": "TEMPERATURE", "celsius": 4.5},
            event_id=None,
            nonce=None,
        )
        self.assertEqual(resp.status_code, 400)

    def test_missing_event_id_and_nonce_rejected_for_sensor_reading(self):
        resp = self.client.post(
            "/api/v1/iot/readings/temperature",
            headers=self._headers(self.device_a),
            json={"device_id": self.device_a["id"], "celsius": 4.5},
        )
        self.assertEqual(resp.status_code, 400)

    def test_stale_timestamp_rejected(self):
        stale = (datetime.now(tz=timezone.utc) - timedelta(hours=25)).isoformat()
        resp = self._post_ingest(
            self.device_a,
            {"event_type": "TEMPERATURE", "celsius": 4.5, "timestamp": stale},
            event_id="evt-stale-ts-1",
        )
        self.assertEqual(resp.status_code, 400)

    def test_same_event_id_across_devices_is_allowed(self):
        payload = {"event_type": "TEMPERATURE", "celsius": 4.5}
        r1 = self._post_ingest(self.device_a, payload, event_id="evt-same-1")
        r2 = self._post_ingest(self.device_b, payload, event_id="evt-same-1")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)

        from app.models.temperature_reading import TemperatureReading
        rows_a = TemperatureReading.query.filter_by(device_id=self.device_a["id"]).all()
        rows_b = TemperatureReading.query.filter_by(device_id=self.device_b["id"]).all()
        self.assertEqual(len(rows_a), 1)
        self.assertEqual(len(rows_b), 1)

    def test_concurrent_duplicate_event_id_only_one_temperature_persisted(self):
        from app.models.temperature_reading import TemperatureReading

        results: list[int] = []
        barrier = threading.Barrier(3)

        def worker():
            # Each worker needs its own app context.
            from app import create_app
            from app.extensions.db import db

            app = create_app()
            app.config["TESTING"] = True
            ctx = app.app_context()
            ctx.push()
            db.create_all()

            barrier.wait()
            from app.services.iot_logistics_service import ingest_device_event, IoTLogisticsError

            try:
                ingest_device_event(
                    "GENERIC",
                    {
                        "event_type": "TEMPERATURE",
                        "device_id": self.device_a["id"],
                        "celsius": 4.5,
                        "event_id": "evt-concurrent-dupe-1",
                    },
                    actor=f"device:{self.device_a['device_code']}",
                    authenticated_device_id=self.device_a["id"],
                    event_id_from_payload="evt-concurrent-dupe-1",
                    offline=False,
                )
                results.append(200)
            except IoTLogisticsError as exc:
                results.append(exc.status_code)
            db.session.remove()
            ctx.pop()

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        barrier.wait()
        t1.join()
        t2.join()

        from app.extensions.db import db
        db.session.expire_all()
        rows = TemperatureReading.query.filter_by(device_id=self.device_a["id"]).all()
        self.assertEqual(len(rows), 1)

    def test_concurrent_nonce_reuse_rejected(self):
        from app.models.temperature_reading import TemperatureReading

        results: list[int] = []
        barrier = threading.Barrier(3)

        def worker():
            from app import create_app
            from app.extensions.db import db

            app = create_app()
            app.config["TESTING"] = True
            ctx = app.app_context()
            ctx.push()
            db.create_all()
            barrier.wait()
            from app.services.iot_logistics_service import ingest_device_event, IoTLogisticsError

            try:
                ingest_device_event(
                    "GENERIC",
                    {
                        "event_type": "TEMPERATURE",
                        "device_id": self.device_a["id"],
                        "celsius": 4.5,
                        "nonce": "n-1",
                    },
                    actor=f"device:{self.device_a['device_code']}",
                    authenticated_device_id=self.device_a["id"],
                    offline=False,
                )
                results.append(200)
            except IoTLogisticsError as exc:
                results.append(exc.status_code)
            db.session.remove()
            ctx.pop()

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        barrier.wait()
        t1.join()
        t2.join()

        from app.extensions.db import db
        db.session.expire_all()
        # Exactly one request should be accepted.
        self.assertEqual(sorted(results), [200, 409])
        rows = TemperatureReading.query.filter_by(device_id=self.device_a["id"]).all()
        self.assertEqual(len(rows), 1)

    def test_replayed_signed_request_idempotent(self):
        payload = {"event_type": "TEMPERATURE", "device_id": self.device_a["id"], "celsius": 4.5, "event_id": "evt-signed-dupe-1"}
        body = json.dumps({"adapter_type": "GENERIC", "payload": payload}, separators=(",", ":")).encode("utf-8")
        sig = hmac.new(self.device_secret.encode("utf-8"), body, digestmod="sha256").hexdigest()
        headers = {"X-Device-Id": self.device_a["id"], "X-Device-Secret": self.device_secret}
        r1 = self._post_ingest_raw_body(self.device_a, payload, headers=headers, signature=sig)
        r2 = self._post_ingest_raw_body(self.device_a, payload, headers=headers, signature=sig)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)


if __name__ == "__main__":
    unittest.main()

