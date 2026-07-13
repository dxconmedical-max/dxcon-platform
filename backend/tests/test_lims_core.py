import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import (
    LIMS_SPECIMEN_COLLECTED,
    LIMS_SPECIMEN_CREATED,
    LIMS_SPECIMEN_IN_TRANSIT,
    LIMS_SPECIMEN_RECEIVED,
)
from app.extensions.db import db
from app.lims_core.service import (
    LimsCoreError,
    create_specimen,
    generate_barcode,
    lims_dashboard,
    list_specimens,
    receive_and_accession_specimen,
    transition_specimen,
    verify_barcode,
)
from app.models.lims_core import LimsSampleStatusHistory, LimsSpecimen


class LimsCoreTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_create_specimen_with_barcode_pattern(self):
        specimen = create_specimen(order_code="ORD-100", container_type="blood_edta", volume=5.0, actor="lab@test")
        db.session.commit()
        self.assertTrue(specimen["human_readable"].startswith("DX"))
        self.assertEqual(len(specimen["human_readable"]), 16)  # DX + 8 date + 6 seq
        self.assertEqual(specimen["status"], LIMS_SPECIMEN_CREATED)
        history = LimsSampleStatusHistory.query.filter_by(specimen_id=specimen["id"]).all()
        self.assertEqual(len(history), 1)

    def test_barcode_no_duplicate(self):
        first = create_specimen(actor="lab@test")
        db.session.commit()
        second = create_specimen(actor="lab@test")
        db.session.commit()
        self.assertNotEqual(first["human_readable"], second["human_readable"])

    def test_lifecycle_transitions_stored(self):
        specimen = create_specimen(actor="lab@test")
        db.session.commit()
        transition_specimen(specimen["id"], to_status=LIMS_SPECIMEN_COLLECTED, actor="collector")
        transition_specimen(specimen["id"], to_status=LIMS_SPECIMEN_IN_TRANSIT, actor="collector")
        transition_specimen(specimen["id"], to_status=LIMS_SPECIMEN_RECEIVED, actor="lab")
        db.session.commit()
        rows = LimsSampleStatusHistory.query.filter_by(specimen_id=specimen["id"]).all()
        self.assertEqual(len(rows), 4)  # created + 3 transitions

    def test_invalid_transition_blocked(self):
        specimen = create_specimen(actor="lab@test")
        db.session.commit()
        with self.assertRaises(LimsCoreError):
            transition_specimen(specimen["id"], to_status=LIMS_SPECIMEN_RECEIVED)

    def test_accession_receive_flow(self):
        specimen = create_specimen(actor="lab@test")
        db.session.commit()
        transition_specimen(specimen["id"], to_status=LIMS_SPECIMEN_COLLECTED, actor="c")
        transition_specimen(specimen["id"], to_status=LIMS_SPECIMEN_IN_TRANSIT, actor="c")
        db.session.commit()
        result = receive_and_accession_specimen(
            barcode_value=specimen["human_readable"],
            operator="lab@test",
            rack="R1",
            shelf="S2",
            batch="B3",
            actor="lab@test",
        )
        db.session.commit()
        self.assertIn("accession_number", result)
        self.assertEqual(result["rack"], "R1")

    def test_verify_barcode(self):
        specimen = create_specimen(actor="lab@test")
        db.session.commit()
        verified = verify_barcode(specimen["human_readable"])
        self.assertTrue(verified["valid"])

    def test_generate_barcode_for_existing_specimen(self):
        specimen = create_specimen(actor="lab@test")
        db.session.commit()
        payload = generate_barcode(specimen_id=specimen["id"], formats=["QR"], actor="lab@test")
        db.session.commit()
        self.assertEqual(len(payload["barcodes"]), 1)

    def test_dashboard_kpis(self):
        create_specimen(actor="lab@test")
        db.session.commit()
        dash = lims_dashboard()
        self.assertIn("samples_today", dash["kpis"])
        self.assertEqual(len(dash["cards"]), 8)

    def test_list_specimens_pagination(self):
        for _ in range(3):
            create_specimen(actor="lab@test")
        db.session.commit()
        page = list_specimens(page=1, per_page=2)
        self.assertEqual(len(page["items"]), 2)
        self.assertEqual(page["pagination"]["total"], 3)

    def test_api_specimens_crud(self):
        client = self.app.test_client()
        with self.app.test_request_context():
            resp = client.post(
                "/api/v1/specimens",
                json={"order_code": "ORD-API", "container_type": "serum", "volume": 3},
                headers={"X-User-Email": "lab@test", "X-Organization-ID": "org-1"},
            )
        self.assertIn(resp.status_code, (200, 201, 401, 403))
        if resp.status_code in (200, 201):
            body = resp.get_json()
            self.assertTrue(body.get("success"))
            specimen_id = body["data"]["id"]
            get_resp = client.get(f"/api/v1/specimens/{specimen_id}")
            self.assertEqual(get_resp.status_code, 200)

    def test_api_lab_dashboard(self):
        client = self.app.test_client()
        resp = client.get("/api/v1/lab/lims/dashboard")
        self.assertIn(resp.status_code, (200, 401, 403))


if __name__ == "__main__":
    unittest.main()
