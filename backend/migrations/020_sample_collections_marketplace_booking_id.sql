-- Authoritative migration: sample_collections.marketplace_booking_id
--
-- Production error:
--   psycopg2.errors.UndefinedColumn:
--   column sample_collections.marketplace_booking_id does not exist
--
-- Matches SQLAlchemy SampleCollection:
--   marketplace_booking_id = db.Column(db.String(36), db.ForeignKey("marketplace_bookings.id"))
--   → VARCHAR(36), NULLABLE, FK → marketplace_bookings(id)
--
-- Idempotent / additive / PostgreSQL-safe. No DROP, no renames, no data rewrite.

-- 1) Column (exact model type + nullability)
ALTER TABLE sample_collections
  ADD COLUMN IF NOT EXISTS marketplace_booking_id VARCHAR(36);

-- 2) Lookup index (queue / ensure / booking filters)
CREATE INDEX IF NOT EXISTS ix_sample_collections_marketplace_booking_id
  ON sample_collections (marketplace_booking_id);

-- 3) Foreign key matching the ORM (only if target table exists; skip if already present)
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

  -- New column is NULL for existing rows, so FK add is safe on greenfield column.
  ALTER TABLE sample_collections
    ADD CONSTRAINT fk_sample_collections_marketplace_booking_id
    FOREIGN KEY (marketplace_booking_id)
    REFERENCES marketplace_bookings (id);
END $$;
