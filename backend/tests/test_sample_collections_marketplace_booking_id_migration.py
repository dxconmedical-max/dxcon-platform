"""Regression: sample_collections.marketplace_booking_id schema + queue compatibility."""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
import uuid
from pathlib import Path

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.services.sample_collection_workflow import SampleCollectionWorkflowService

_SCRIPT = ROOT / "scripts" / "apply_sample_collections_marketplace_booking_id.py"
_SPEC = importlib.util.spec_from_file_location("apply_sc_mbid", _SCRIPT)
_MOD = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_MOD)


class MarketplaceBookingIdSchemaTestCase(unittest.TestCase):
    def test_migration_file_adds_marketplace_booking_id(self):
        sql = _MOD.MIGRATION_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "ADD COLUMN IF NOT EXISTS marketplace_booking_id VARCHAR(36)",
            sql,
        )
        self.assertIn("REFERENCES marketplace_bookings (id)", sql)
        self.assertNotIn("DROP COLUMN", sql.upper())

    def test_queue_works_on_legacy_schema_without_marketplace_booking_id(self):
        """Production-shaped Phase-1 table must not 500 on GET queue."""
        app = create_app()
        with app.app_context():
            db.session.execute(text("DROP TABLE IF EXISTS sample_collections"))
            db.session.execute(
                text(
                    """
                    CREATE TABLE sample_collections (
                        id VARCHAR(36) PRIMARY KEY,
                        order_id VARCHAR(36) NOT NULL,
                        collector_name VARCHAR(255),
                        status VARCHAR(50),
                        collected_at DATETIME,
                        created_at DATETIME
                    )
                    """
                )
            )
            row_id = str(uuid.uuid4())
            db.session.execute(
                text(
                    "INSERT INTO sample_collections (id, order_id, status, created_at) "
                    "VALUES (:id, :oid, 'PENDING', CURRENT_TIMESTAMP)"
                ),
                {"id": row_id, "oid": str(uuid.uuid4())},
            )
            db.session.commit()

            items = SampleCollectionWorkflowService.list_queue(awaiting_only=True)
            self.assertGreaterEqual(len(items), 1)
            self.assertEqual(items[0]["id"], row_id)
            self.assertIsNone(items[0].get("marketplace_booking_id"))
            self.assertEqual(items[0]["status"], "PENDING")


if __name__ == "__main__":
    unittest.main()
