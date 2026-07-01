import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.integrations.adapter_loader import load_adapters
from app.integrations.adapter_manager import AdapterManager
from app.integrations.adapter_registry import AdapterRegistry


class AdapterFrameworkTestCase(unittest.TestCase):
    def setUp(self):
        AdapterRegistry.reset()
        load_adapters()

    def test_demo_adapters_register(self):
        types = AdapterRegistry.list_types()
        self.assertEqual(len(types), 8)
        self.assertIn("HIS", types)
        self.assertIn("LIS", types)

    def test_adapter_lifecycle(self):
        connect = AdapterManager.connect("HIS")
        self.assertEqual(connect["status"], "CONNECTED")
        health = AdapterManager.health_check("HIS")
        self.assertEqual(health["status"], "OK")
        sent = AdapterManager.send("HIS", {"patient_id": "P1"})
        self.assertEqual(sent["status"], "ACCEPTED")
        received = AdapterManager.receive("HIS", {"patient_id": "P1"})
        self.assertEqual(received["status"], "RECEIVED")
        disconnected = AdapterManager.disconnect("HIS")
        self.assertEqual(disconnected["status"], "DISCONNECTED")

    def test_transform_and_validate(self):
        transformed = AdapterManager.transform("ERP", {"order_id": "O1"}, direction="outbound")
        self.assertEqual(transformed["adapter"], "ERP")
        validation = AdapterManager.validate("ERP", transformed)
        self.assertTrue(validation["valid"])


if __name__ == "__main__":
    unittest.main()
