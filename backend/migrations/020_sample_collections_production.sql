-- Sample Collection production columns — additive, idempotent.
-- Aligns live PostgreSQL with SampleCollection ORM fields.
--
-- History:
--   Phase-1 table often only had: id, order_id, collector_name, status,
--   collected_at, created_at (created via db.create_all / ad-hoc).
--   Release 0.4 added marketplace_booking_id, collector_id, sample_tracking_id
--   without a SQL migration.
--   Later production workflow added specimen/transport columns without a migration.
--
-- CREATE TABLE IF NOT EXISTS does NOT add columns to an existing table.
-- Every ORM column must therefore be covered by ADD COLUMN IF NOT EXISTS.
--
-- Safe to re-run. Does not drop columns or rewrite existing rows.

CREATE TABLE IF NOT EXISTS sample_collections (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,
    marketplace_booking_id VARCHAR(36),
    collector_id VARCHAR(36),
    sample_tracking_id VARCHAR(36),
    collector_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'PENDING',
    collected_at TIMESTAMP,
    created_at TIMESTAMP
);

-- Release 0.4 booking / assignment link columns (missing on some production DBs)
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS marketplace_booking_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS sample_tracking_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collector_name VARCHAR(255);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collected_at TIMESTAMP;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS created_at TIMESTAMP;

-- Production Sample Collection workflow columns
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
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS picked_up_at TIMESTAMP;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS dispatched_at TIMESTAMP;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS handoff_at TIMESTAMP;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS arrived_at_lab TIMESTAMP;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS vehicle_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS driver_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS transport_box_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS distance_km DOUBLE PRECISION;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS eta_minutes INTEGER;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS temperature_c DOUBLE PRECISION;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS iot_device_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS ix_sample_collections_status ON sample_collections(status);
CREATE INDEX IF NOT EXISTS ix_sample_collections_collector_id ON sample_collections(collector_id);
CREATE INDEX IF NOT EXISTS ix_sample_collections_partner_id ON sample_collections(partner_id);
CREATE INDEX IF NOT EXISTS ix_sample_collections_created_at ON sample_collections(created_at);
CREATE INDEX IF NOT EXISTS ix_sample_collections_marketplace_booking_id ON sample_collections(marketplace_booking_id);
