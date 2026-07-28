-- Collection mode routing — additive, idempotent.
--
-- Authoritative routing field: sample_collections.collection_mode
-- Values: AT_RECEPTION | HOME_COLLECTION | CLINIC_COLLECTION
--
-- Replaces inference via source=desk / null marketplace_booking_id / notes.

CREATE TABLE IF NOT EXISTS sample_collections (
    id VARCHAR(36) PRIMARY KEY,
    order_id VARCHAR(36) NOT NULL,
    collector_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'PENDING',
    collected_at TIMESTAMP,
    created_at TIMESTAMP
);

ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collection_mode VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_address VARCHAR(500);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_city VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS requested_date VARCHAR(20);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS requested_time_window VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_latitude VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_longitude VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collection_request_note TEXT;

-- Deterministic backfill (never overwrite an already-set mode).
-- AT_RECEPTION: PR #10 desk markers
UPDATE sample_collections
SET collection_mode = 'AT_RECEPTION'
WHERE collection_mode IS NULL
  AND (
    notes ILIKE '%source:desk%'
    OR LOWER(COALESCE(collection_location, '')) = 'reception desk'
    OR LOWER(COALESCE(collector_name, '')) = 'walk-in collector'
  );

-- HOME_COLLECTION: marketplace / field bookings with a booking id
UPDATE sample_collections
SET collection_mode = 'HOME_COLLECTION'
WHERE collection_mode IS NULL
  AND marketplace_booking_id IS NOT NULL
  AND marketplace_booking_id <> '';

-- Ambiguous leftovers stay NULL for reporting (do not guess CLINIC vs HOME).
-- Query: SELECT id, order_id, status, notes, marketplace_booking_id
--        FROM sample_collections WHERE collection_mode IS NULL;

CREATE INDEX IF NOT EXISTS ix_sample_collections_collection_mode
    ON sample_collections (collection_mode);

CREATE INDEX IF NOT EXISTS ix_sample_collections_mode_status
    ON sample_collections (collection_mode, status);
