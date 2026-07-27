-- Sample Collection production columns — additive, idempotent.
-- Aligns live PostgreSQL with SampleCollection ORM fields added for field
-- queue / verify / collect / transport (commit 01efd5f) which shipped without
-- a migration. Missing columns cause:
--   GET /api/v1/sample-collections/queue → OperationalError/ProgrammingError → HTTP 500
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
