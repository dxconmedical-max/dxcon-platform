"""Regression tests for GET /api/v1/sample-collections/queue (production 500 hotfix)."""

from __future__ import annotations

import os
import sys
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from flask_jwt_extended import create_access_token
from sqlalchemy import text

from app import create_app
from app.core.statuses import COLLECTION_PENDING, MAPPING_ACTIVE, PARTNER_ACTIVE
from app.extensions.db import db
from app.models.diagnostic_category import DiagnosticCategory
from app.models.diagnostic_service import DiagnosticService
from app.models.driver import Driver
from app.models.partner import Partner
from app.models.partner_service_mapping import PartnerServiceMapping
from app.models.sample_collection import SampleCollection
from app.models.user import User
from app.services.booking_assignment import BookingAssignmentService
from app.services.marketplace_booking import MarketplaceBookingService
from app.services.order_lifecycle import OrderLifecycleService
from app.services.sample_collection_workflow import (
    SampleCollectionWorkflowError,
    SampleCollectionWorkflowService,
)
from app.services.scheduling import SchedulingService
from app.services.slot_generation import SlotGenerationService
from app.sample_collection_workspace.service import list_production_queue

ORG_ID = "00000000-0000-4000-8000-000000000001"
# Release 0.4 booking-link columns — must be ALTER'd (CREATE TABLE IF NOT EXISTS
# does not retrofit existing production tables).
BOOKING_LINK_COLUMNS = (
    "marketplace_booking_id",
    "collector_id",
    "sample_tracking_id",
)
PRODUCTION_COLUMNS = (
    "specimen_type",
    "barcode_value",
    "expected_barcode",
    "collection_location",
    "location_city",
    "notes",
    "quality_status",
    "rejection_reason",
    "partner_id",
    "recollect_of_id",
    "patient_verified",
    "order_verified",
    "picked_up_at",
    "dispatched_at",
    "handoff_at",
    "arrived_at_lab",
    "vehicle_id",
    "driver_id",
    "transport_box_id",
    "distance_km",
    "eta_minutes",
    "temperature_c",
    "iot_device_id",
    "updated_at",
)


def _apply_sql_migration(path: Path) -> None:
    """Apply additive SQL migration statements (SQLite-friendly subset)."""
    import re

    sql = path.read_text(encoding="utf-8")
    lines = [
        ln
        for ln in sql.splitlines()
        if ln.strip() and not ln.strip().startswith("--")
    ]
    body = "\n".join(lines)
    for stmt in body.split(";"):
        stmt = stmt.strip()
        if not stmt:
            continue
        m = re.match(
            r"ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS (\w+) (.+)",
            stmt,
            re.I,
        )
        if m:
            col, typ = m.group(1), m.group(2)
            typ = (
                typ.replace("DOUBLE PRECISION", "REAL")
                .replace("BOOLEAN", "INTEGER")
                .replace("TIMESTAMP", "DATETIME")
            )
            try:
                db.session.execute(
                    text(f"ALTER TABLE sample_collections ADD COLUMN {col} {typ}")
                )
                db.session.commit()
            except Exception:
                db.session.rollback()
            continue
        if stmt.upper().startswith("CREATE TABLE"):
            continue
        if stmt.upper().startswith("CREATE INDEX"):
            try:
                db.session.execute(text(stmt))
                db.session.commit()
            except Exception:
                db.session.rollback()
            continue
        try:
            db.session.execute(text(stmt))
            db.session.commit()
        except Exception:
            db.session.rollback()


class SampleCollectionQueueTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        category = DiagnosticCategory(
            category_code="BIOCHEM-Q",
            name="Biochemistry Queue",
            is_active=True,
        )
        db.session.add(category)
        db.session.flush()
        self.service = DiagnosticService(
            service_code="HBA1C-Q",
            name="HbA1c Queue",
            category_id=category.id,
            estimated_turnaround_hours=24,
            is_active=True,
        )
        db.session.add(self.service)

        self.partner_a = Partner(
            partner_code="PTR-Q-A",
            partner_type="LABORATORY",
            legal_name="Queue Lab A",
            display_name="Queue Lab A",
            city="Ha Noi",
            status=PARTNER_ACTIVE,
        )
        self.partner_b = Partner(
            partner_code="PTR-Q-B",
            partner_type="LABORATORY",
            legal_name="Queue Lab B",
            display_name="Queue Lab B",
            city="Da Nang",
            status=PARTNER_ACTIVE,
        )
        db.session.add_all([self.partner_a, self.partner_b])
        db.session.flush()

        self.mapping_a = PartnerServiceMapping(
            partner_id=self.partner_a.id,
            diagnostic_service_id=self.service.id,
            partner_service_code="QA-HBA1C",
            partner_service_name="HbA1c",
            price=180000,
            status=MAPPING_ACTIVE,
        )
        db.session.add(self.mapping_a)

        self.collector = Driver(
            driver_code="COL-Q-001",
            full_name="Queue Collector",
            status="ACTIVE",
        )
        db.session.add(self.collector)

        self.super_admin = User(
            email=f"super-{uuid.uuid4().hex[:6]}@test.local",
            role="SUPER_ADMIN",
            password_hash="x",
            is_active=True,
        )
        self.collector_user = User(
            email=f"collector-{uuid.uuid4().hex[:6]}@test.local",
            role="COLLECTOR",
            password_hash="x",
            is_active=True,
        )
        self.denied_user = User(
            email=f"patient-{uuid.uuid4().hex[:6]}@test.local",
            role="PATIENT",
            password_hash="x",
            is_active=True,
        )
        db.session.add_all([self.super_admin, self.collector_user, self.denied_user])
        db.session.commit()

        SlotGenerationService.generate_partner_daily_slots(self.partner_a.id, days=2)
        SlotGenerationService.generate_collector_availability(
            self.collector.id,
            days=2,
            city="Ha Noi",
            district="Cau Giay",
        )

        self.super_token = create_access_token(
            identity=self.super_admin.id,
            additional_claims={"role": "SUPER_ADMIN"},
        )
        self.denied_token = create_access_token(
            identity=self.denied_user.id,
            additional_claims={"role": "PATIENT"},
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _auth(self, token: str, **extra_headers):
        headers = {
            "Authorization": f"Bearer {token}",
            "X-Organization-Id": ORG_ID,
        }
        headers.update(extra_headers)
        return headers

    def _assigned_booking(self, phone_suffix="2001"):
        slot = SchedulingService.list_available_slots(self.partner_a.id)[0]
        booking = MarketplaceBookingService.create_booking(
            {
                "partner_service_mapping_id": self.mapping_a.id,
                "patient_name": "Queue Patient",
                "patient_phone": f"090777{phone_suffix}",
                "patient_address": "12 Cau Giay, Ha Noi",
                "requested_date": slot.slot_date,
            }
        )
        BookingAssignmentService.reserve_slot_for_booking(booking.id, slot.id)
        BookingAssignmentService.assign_collector(booking.id, self.collector.id)
        OrderLifecycleService.create_order_from_booking(booking.id)
        return booking

    def _session_as(self, user):
        with self.client.session_transaction() as sess:
            sess["user_id"] = user.id
            sess["role"] = user.role
            sess["email"] = user.email

    def test_migration_lists_all_orm_columns_as_alter(self):
        migration_020 = (
            ROOT / "migrations" / "020_sample_collections_production.sql"
        ).read_text(encoding="utf-8")
        migration_021 = (
            ROOT / "migrations" / "021_sample_collections_booking_link.sql"
        ).read_text(encoding="utf-8")
        for column in BOOKING_LINK_COLUMNS:
            self.assertIn(
                f"ADD COLUMN IF NOT EXISTS {column}",
                migration_020,
                msg=f"020 missing ALTER for {column}",
            )
            self.assertIn(
                f"ADD COLUMN IF NOT EXISTS {column}",
                migration_021,
                msg=f"021 missing ALTER for {column}",
            )
        for column in PRODUCTION_COLUMNS:
            self.assertIn(
                f"ADD COLUMN IF NOT EXISTS {column}",
                migration_020,
                msg=f"migration missing column {column}",
            )

    def test_include_desk_false(self):
        booking = self._assigned_booking("2101")
        collection = SampleCollectionWorkflowService.ensure_collection_for_booking(booking.id)
        resp = self.client.get(
            "/api/v1/sample-collections/queue?include_desk=false",
            headers=self._auth(self.super_token),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["success"])
        data = body["data"]
        self.assertIn("items", data)
        self.assertIn("count", data)
        self.assertGreaterEqual(data["count"], 1)
        self.assertTrue(any(item["id"] == collection.id for item in data["items"]))
        self.assertTrue(all(item.get("source") != "desk" for item in data["items"]))

    def test_include_desk_true(self):
        booking = self._assigned_booking("2103")
        SampleCollectionWorkflowService.ensure_collection_for_booking(booking.id)
        resp = self.client.get(
            "/api/v1/sample-collections/queue?include_desk=true",
            headers=self._auth(self.super_token),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["success"])
        self.assertIn("items", body["data"])
        self.assertIn("desk_count", body["data"])

    def test_include_desk_omitted_defaults_to_true(self):
        booking = self._assigned_booking("2104")
        SampleCollectionWorkflowService.ensure_collection_for_booking(booking.id)
        resp = self.client.get(
            "/api/v1/sample-collections/queue",
            headers=self._auth(self.super_token),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()["data"]
        self.assertIn("desk_count", data)
        self.assertIn("field_count", data)

    def test_empty_queue_returns_200(self):
        resp = self.client.get(
            "/api/v1/sample-collections/queue?include_desk=false",
            headers=self._auth(self.super_token),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["items"], [])
        self.assertEqual(body["data"]["count"], 0)

    def test_nullable_relationships_do_not_500(self):
        orphan = SampleCollection(
            order_id=str(uuid.uuid4()),
            marketplace_booking_id=str(uuid.uuid4()),  # dangling
            sample_tracking_id=str(uuid.uuid4()),  # dangling
            status=COLLECTION_PENDING,
            partner_id=self.partner_a.id,
            location_city="Ha Noi",
        )
        db.session.add(orphan)
        db.session.commit()

        payload = SampleCollectionWorkflowService._enrich_payload(orphan)
        self.assertIsNone(payload["booking"])
        self.assertIsNone(payload["order"])
        self.assertIsNone(payload["sample_tracking"])

        resp = self.client.get(
            "/api/v1/sample-collections/queue?include_desk=false",
            headers=self._auth(self.super_token),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["success"])
        ids = {item["id"] for item in resp.get_json()["data"]["items"]}
        self.assertIn(orphan.id, ids)

    def test_super_admin_access(self):
        resp = self.client.get(
            "/api/v1/sample-collections/queue?include_desk=false",
            headers=self._auth(self.super_token),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["success"])

    def test_insufficient_role_forbidden(self):
        resp = self.client.get(
            "/api/v1/sample-collections/queue?include_desk=false",
            headers=self._auth(self.denied_token),
        )
        self.assertEqual(resp.status_code, 403)
        body = resp.get_json()
        self.assertFalse(body.get("success", True))
        error = body.get("error")
        self.assertIsInstance(error, dict)
        self.assertIn("message", error)
        self.assertNotEqual(str(error), "[object Object]")

    def test_organization_header_does_not_500(self):
        resp = self.client.get(
            "/api/v1/sample-collections/queue?include_desk=false",
            headers=self._auth(self.super_token),
        )
        self.assertEqual(resp.status_code, 200)

    def test_partner_scoping_no_cross_tenant_leakage(self):
        booking = self._assigned_booking("2201")
        collection = SampleCollectionWorkflowService.ensure_collection_for_booking(booking.id)
        collection.partner_id = self.partner_a.id
        other = SampleCollection(
            order_id=str(uuid.uuid4()),
            status=COLLECTION_PENDING,
            partner_id=self.partner_b.id,
            location_city="Da Nang",
        )
        db.session.add(other)
        db.session.commit()

        scoped = list_production_queue(
            partner_id=self.partner_a.id,
            include_desk=False,
            role="SUPER_ADMIN",
        )
        ids = {item["id"] for item in scoped["items"]}
        self.assertIn(collection.id, ids)
        self.assertNotIn(other.id, ids)

        resp = self.client.get(
            f"/api/v1/sample-collections/queue?include_desk=false&partner_id={self.partner_a.id}",
            headers=self._auth(self.super_token),
        )
        self.assertEqual(resp.status_code, 200)
        api_ids = {item["id"] for item in resp.get_json()["data"]["items"]}
        self.assertIn(collection.id, api_ids)
        self.assertNotIn(other.id, api_ids)

    def test_invalid_date_returns_structured_400(self):
        resp = self.client.get(
            "/api/v1/sample-collections/queue?include_desk=false&date_from=not-a-date",
            headers=self._auth(self.super_token),
        )
        self.assertEqual(resp.status_code, 400)
        body = resp.get_json()
        self.assertFalse(body["success"])
        self.assertIsInstance(body["error"], dict)
        self.assertIn("message", body["error"])

    def test_legacy_schema_missing_columns_returns_readable_503_not_opaque_500(self):
        """Reproduce production failure mode: ORM columns absent from physical table."""
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
        db.session.execute(
            text(
                "INSERT INTO sample_collections (id, order_id, status, created_at) "
                "VALUES (:id, :oid, 'PENDING', CURRENT_TIMESTAMP)"
            ),
            {"id": str(uuid.uuid4()), "oid": str(uuid.uuid4())},
        )
        db.session.commit()

        with self.assertRaises(SampleCollectionWorkflowError) as ctx:
            SampleCollectionWorkflowService.list_queue(awaiting_only=True)
        self.assertEqual(ctx.exception.status_code, 503)
        self.assertIn("sample_collections", ctx.exception.message.lower())

        resp = self.client.get(
            "/api/v1/sample-collections/queue?include_desk=false",
            headers=self._auth(self.super_token),
        )
        self.assertEqual(resp.status_code, 503)
        error = resp.get_json()["error"]
        self.assertIsInstance(error, dict)
        self.assertIn("message", error)

    def test_production_missing_marketplace_booking_id_fixed_by_migration(self):
        """Exact production UndefinedColumn: marketplace_booking_id missing."""
        db.session.execute(text("DROP TABLE IF EXISTS sample_collections"))
        # Phase-1 shaped table (no booking link columns) — matches live traceback.
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

        with self.assertRaises(SampleCollectionWorkflowError) as ctx:
            SampleCollectionWorkflowService.list_queue(awaiting_only=True)
        self.assertEqual(ctx.exception.status_code, 503)

        _apply_sql_migration(ROOT / "migrations" / "020_sample_collections_production.sql")
        _apply_sql_migration(ROOT / "migrations" / "021_sample_collections_booking_link.sql")

        # SQLAlchemy metadata may still think columns were always there; clear
        # identity map and re-query via ORM after physical ALTER.
        db.session.expire_all()
        items = SampleCollectionWorkflowService.list_queue(awaiting_only=True)
        self.assertGreaterEqual(len(items), 1)
        self.assertTrue(any(item["id"] == row_id for item in items))

        resp = self.client.get(
            "/api/v1/sample-collections/queue?include_desk=false",
            headers=self._auth(self.super_token),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["success"])
        self.assertEqual(resp.get_json()["data"]["count"], len(items))


if __name__ == "__main__":
    unittest.main()
