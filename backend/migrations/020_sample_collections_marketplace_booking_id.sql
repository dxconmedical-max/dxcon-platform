-- Sample Collection production schema alignment — additive, idempotent.
--
-- Production traceback:
--   psycopg2.errors.UndefinedColumn:
--   column sample_collections.marketplace_booking_id does not exist
--
-- Root cause: SampleCollection ORM (Release 0.4+) maps marketplace_booking_id
-- and later production workflow columns, but live Postgres still has a Phase-1
-- table. SQLAlchemy SELECTs every mapped column on GET /queue → UndefinedColumn.
--
-- No Alembic in this repo — numbered SQL migrations under backend/migrations/.
-- Safe to re-run. No DROP / rename / data rewrite.

CREATE TABLE IF NOT EXISTS sample_collections (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,
    collector_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'PENDING',
    collected_at TIMESTAMP,
    created_at TIMESTAMP
);

-- Release 0.4 booking / assignment link (authoritative for marketplace_booking_id)
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS marketplace_booking_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS sample_tracking_id VARCHAR(36);

-- Later production workflow columns (also selected by ORM on /queue)
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
CREATE INDEX IF NOT EXISTS ix_sample_collections_marketplace_booking_id
  ON sample_collections (marketplace_booking_id);

-- FK matching ORM ForeignKey("marketplace_bookings.id") — only if target exists
DO $$
BEGIN
  IF to_regclass('public.marketplace_bookings') IS NULL THEN
    RAISE NOTICE 'marketplace_bookings missing — column added without FK';
    RETURN;
  END IF;

  IF EXISTS (
    SELECT 1
    FROM information_schema.table_constraints
    WHERE table_schema = 'public'
      AND table_name = 'sample_collections'
      AND constraint_name = 'fk_sample_collections_marketplace_booking_id'
  ) THEN
    RETURN;
  END IF;

  ALTER TABLE sample_collections
    ADD CONSTRAINT fk_sample_collections_marketplace_booking_id
    FOREIGN KEY (marketplace_booking_id)
    REFERENCES marketplace_bookings (id);
END $$;
