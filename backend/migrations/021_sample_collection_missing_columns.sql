-- SampleCollection ORM ↔ Postgres schema sync — additive, idempotent.
--
-- Source of truth: backend/app/models/sample_collection.py
--
-- Production risk: SQLAlchemy SELECTs every mapped column. Any ORM field absent
-- from live Postgres raises UndefinedColumn on sample-collection APIs.
--
-- Rules (production-safe):
--   * additive column adds with IF NOT EXISTS
--   * never DROP
--   * never ALTER existing column types
--   * PostgreSQL only
--
-- Safe to re-run after 020 / prior 021 partial applies.

CREATE TABLE IF NOT EXISTS sample_collections (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,
    collector_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'PENDING',
    collected_at TIMESTAMP,
    created_at TIMESTAMP
);

-- Phase-1 base columns (ADD if an older table predates CREATE TABLE shape)
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collector_name VARCHAR(255);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collected_at TIMESTAMP;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;

-- Release 0.4+ booking / assignment
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS marketplace_booking_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS sample_tracking_id VARCHAR(36);

-- Authoritative collection routing
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collection_mode VARCHAR(50);

-- Production specimen / quality / verification
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS specimen_type VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS barcode_value VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS expected_barcode VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collection_location VARCHAR(255);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS location_city VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS quality_status VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS recollect_of_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS patient_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS order_verified BOOLEAN DEFAULT FALSE;

-- Transport / lab arrival timestamps
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS picked_up_at TIMESTAMP;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS dispatched_at TIMESTAMP;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS handoff_at TIMESTAMP;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS arrived_at_lab TIMESTAMP;

-- Logistics / IoT
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS vehicle_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS driver_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS transport_box_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS distance_km DOUBLE PRECISION;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS eta_minutes INTEGER;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS temperature_c DOUBLE PRECISION;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS iot_device_id VARCHAR(36);

-- Field collection request metadata (HOME / CLINIC)
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_address VARCHAR(500);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_city VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_province VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_district VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_ward VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS contact_person VARCHAR(255);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS requested_date VARCHAR(20);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS requested_time_window VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_latitude VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_longitude VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collection_request_note TEXT;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS clinic_name VARCHAR(255);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS priority VARCHAR(50);

-- ORM updated_at
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
