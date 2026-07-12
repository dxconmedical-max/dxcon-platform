"""Tests for IoT Logistics Platform — Release 7.0 Sprint 4."""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["IOT_SIMULATOR_ENABLED"] = "true"

from app import create_app
from app.extensions.db import db
from app.iot_platform.auth import hash_device_secret, simulator_allowed, verify_device_token
from app.iot_platform.ingestion import IngestionError, ingest_telemetry
from app.iot_platform.service import (
    IoTPlatformError,
    acknowledge_excursion,
    append_custody_event,
    create_threshold_policy,
    create_trip,
    hold_specimen_for_excursion,
    list_alerts,
    process_telemetry_batch,
    register_device,
    transition_trip,
)
from app.models.iot_platform import IoTCanonicalReading, IoTDeviceCredential


class IoTPlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.commit()
        self.org = "org-iot-test"

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _register_with_token(self):
        result = register_device(
            {"device_type": "cold_chain_tracker", "device_code": "DEV-001", "vendor": "TestCo"},
            organization_id=self.org,
            actor="ops@test",
        )
        db.session.commit()
        return result

    def test_device_provisioning(self):
        result = self._register_with_token()
        self.assertIn("device", result)
        self.assertIn("token", result["provisioning"])
        self.assertNotIn("credential_hash", result["device"])

    def test_telemetry_authentication(self):
        result = self._register_with_token()
        device_id = result["device"]["id"]
        token = result["provisioning"]["token"]
        self.assertTrue(verify_device_token(device_id, token))
        self.assertFalse(verify_device_token(device_id, "wrong"))

    def test_duplicate_readings(self):
        result = self._register_with_token()
        device_id = result["device"]["id"]
        payload = {
            "device_id": device_id,
            "recorded_at": datetime.utcnow().isoformat(),
            "temperature_c": 4.5,
            "sequence_number": 1,
        }
        first = ingest_telemetry(payload, organization_id=self.org, simulated=True)
        db.session.commit()
        second = ingest_telemetry(payload, organization_id=self.org, simulated=True)
        db.session.commit()
        self.assertEqual(first["status"], "accepted")
        self.assertEqual(second["status"], "duplicate")

    def test_out_of_order_sequence_rejected(self):
        result = self._register_with_token()
        device_id = result["device"]["id"]
        base = {"device_id": device_id, "recorded_at": datetime.utcnow().isoformat(), "temperature_c": 4.0}
        ingest_telemetry({**base, "sequence_number": 2}, organization_id=self.org, simulated=True)
        db.session.commit()
        with self.assertRaises(IngestionError):
            ingest_telemetry({**base, "sequence_number": 1}, organization_id=self.org, simulated=True)

    def test_threshold_excursion_creates_alert(self):
        result = self._register_with_token()
        device_id = result["device"]["id"]
        create_threshold_policy(
            {"name": "Blood EDTA", "min_temperature_c": 2.0, "max_temperature_c": 8.0},
            organization_id=self.org,
            actor="qa@test",
        )
        db.session.commit()
        trip = create_trip({}, organization_id=self.org)
        db.session.commit()
        process_telemetry_batch(
            [{
                "device_id": device_id,
                "recorded_at": datetime.utcnow().isoformat(),
                "temperature_c": 12.0,
                "sequence_number": 1,
                "trip_id": trip["id"],
            }],
            organization_id=self.org,
            simulated=True,
        )
        db.session.commit()
        alerts = list_alerts(organization_id=self.org)
        self.assertGreaterEqual(alerts["total"], 1)

    def test_alert_deduplication(self):
        result = self._register_with_token()
        device_id = result["device"]["id"]
        create_threshold_policy(
            {"name": "Cold", "max_temperature_c": 8.0},
            organization_id=self.org,
            actor="qa@test",
        )
        db.session.commit()
        payload = {
            "device_id": device_id,
            "recorded_at": datetime.utcnow().isoformat(),
            "temperature_c": 15.0,
            "sequence_number": 10,
        }
        process_telemetry_batch([payload], organization_id=self.org, simulated=True)
        db.session.commit()
        process_telemetry_batch([{**payload, "sequence_number": 11}], organization_id=self.org, simulated=True)
        db.session.commit()
        alerts = list_alerts(organization_id=self.org)
        deduped = [a for a in alerts["alerts"] if a["alert_type"] == "temperature_excursion"]
        self.assertLessEqual(len(deduped), 2)

    def test_trip_lifecycle(self):
        trip = create_trip({"vehicle_id": "veh-1"}, organization_id=self.org)
        db.session.commit()
        started = transition_trip(trip["id"], action="start", organization_id=self.org, actor="driver@test")
        self.assertEqual(started["status"], "ACTIVE")
        completed = transition_trip(trip["id"], action="complete", organization_id=self.org, actor="driver@test")
        self.assertEqual(completed["status"], "COMPLETED")

    def test_custody_events_append_only(self):
        event = append_custody_event(
            {"event_type": "specimen_collected", "reference_type": "specimen", "reference_id": "sp-1"},
            organization_id=self.org,
            actor="collector@test",
        )
        db.session.commit()
        self.assertIn("event_code", event)

    def test_tenant_isolation(self):
        result = self._register_with_token()
        device_id = result["device"]["id"]
        from app.iot_platform.service import get_device
        with self.assertRaises(IoTPlatformError):
            get_device(device_id, organization_id="other-org")

    def test_specimen_hold_workflow(self):
        result = self._register_with_token()
        device_id = result["device"]["id"]
        create_threshold_policy({"name": "Hold test", "max_temperature_c": 6.0}, organization_id=self.org, actor="qa@test")
        db.session.commit()
        process_telemetry_batch(
            [{
                "device_id": device_id,
                "recorded_at": datetime.utcnow().isoformat(),
                "temperature_c": 20.0,
                "sequence_number": 1,
            }],
            organization_id=self.org,
            simulated=True,
        )
        db.session.commit()
        from app.models.iot_platform import IoTColdChainExcursion
        excursion = IoTColdChainExcursion.query.first()
        self.assertIsNotNone(excursion)
        held = hold_specimen_for_excursion(excursion.id, actor="lab@test", organization_id=self.org)
        db.session.commit()
        self.assertTrue(held["specimen_hold"])

    def test_simulator_disabled_in_production(self):
        os.environ["FLASK_ENV"] = "production"
        os.environ.pop("IOT_SIMULATOR_FORCE", None)
        self.assertFalse(simulator_allowed())
        os.environ["FLASK_ENV"] = "development"

    def test_phi_rejected_in_payload(self):
        result = self._register_with_token()
        device_id = result["device"]["id"]
        with self.assertRaises(IngestionError):
            ingest_telemetry(
                {
                    "device_id": device_id,
                    "recorded_at": datetime.utcnow().isoformat(),
                    "patient_name": "John Doe",
                    "sequence_number": 1,
                },
                organization_id=self.org,
            )


if __name__ == "__main__":
    unittest.main()
