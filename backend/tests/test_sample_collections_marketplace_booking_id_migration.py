"""Tests for marketplace_booking_id migration + Flask runner helpers."""

from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

_SCRIPT = ROOT / "scripts" / "apply_sample_collections_marketplace_booking_id.py"
_SPEC = importlib.util.spec_from_file_location("apply_sc_mbid", _SCRIPT)
_MOD = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(_MOD)


class MarketplaceBookingIdMigrationTestCase(unittest.TestCase):
    def test_migration_file_exists(self):
        self.assertTrue(_MOD.MIGRATION_PATH.exists(), msg=_MOD.MIGRATION_NAME)

    def test_migration_adds_exact_model_column(self):
        sql = _MOD.MIGRATION_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "ADD COLUMN IF NOT EXISTS marketplace_booking_id VARCHAR(36)",
            sql,
        )
        self.assertIn("REFERENCES marketplace_bookings (id)", sql)
        self.assertIn("ix_sample_collections_marketplace_booking_id", sql)
        self.assertIn("fk_sample_collections_marketplace_booking_id", sql)
        upper = sql.upper()
        self.assertNotIn("DROP COLUMN", upper)
        self.assertNotIn("DROP TABLE", upper)
        self.assertNotIn("RENAME COLUMN", upper)

    def test_split_sql_preserves_do_block(self):
        sql = _MOD.MIGRATION_PATH.read_text(encoding="utf-8")
        stmts = _MOD._split_sql(sql)
        self.assertGreaterEqual(len(stmts), 3)
        self.assertTrue(
            any("ADD COLUMN IF NOT EXISTS marketplace_booking_id" in s for s in stmts)
        )
        self.assertTrue(any(s.strip().upper().startswith("DO $$") for s in stmts))
        self.assertEqual(_MOD.REQUIRED_COLUMN, "marketplace_booking_id")

    def test_information_schema_verification_query_present(self):
        source = _SCRIPT.read_text(encoding="utf-8")
        self.assertIn("information_schema.columns", source)
        self.assertIn("marketplace_booking_id", source)
        self.assertIn("with app.app_context()", source)


if __name__ == "__main__":
    unittest.main()
