"""Migration 021 collection_mode presence + backfill mapping."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

_TEST_DB = tempfile.NamedTemporaryFile(prefix="dxcon_m021_", suffix=".db", delete=False)
_TEST_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.name}"

ROOT = Path(__file__).resolve().parents[1]

from app import create_app
from app.extensions.db import db
from app.models.sample_collection import SampleCollection
from app.sample_collection_workspace.collection_domain import (
    MODE_AT_RECEPTION,
    MODE_HOME_COLLECTION,
    infer_legacy_mode,
)


class CollectionModeMigrationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_migration_file_exists(self):
        path = ROOT / "migrations" / "021_sample_collections_collection_mode.sql"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn("collection_mode", text)
        self.assertIn("AT_RECEPTION", text)

    def test_infer_legacy_mode_deterministic(self):
        desk = SampleCollection(
            order_id="o1",
            status="PENDING",
            notes="source:desk",
            collection_location="Reception Desk",
            collector_name="Walk-in Collector",
        )
        mode, reason = infer_legacy_mode(desk)
        self.assertEqual(mode, MODE_AT_RECEPTION)
        self.assertEqual(reason, "desk_markers")

        field = SampleCollection(
            order_id="o2",
            status="PENDING",
            marketplace_booking_id="bk-1",
        )
        mode2, reason2 = infer_legacy_mode(field)
        self.assertEqual(mode2, MODE_HOME_COLLECTION)
        self.assertEqual(reason2, "marketplace_booking_id")

        amb = SampleCollection(order_id="o3", status="PENDING")
        mode3, reason3 = infer_legacy_mode(amb)
        self.assertIsNone(mode3)
        self.assertEqual(reason3, "ambiguous")


if __name__ == "__main__":
    unittest.main()
