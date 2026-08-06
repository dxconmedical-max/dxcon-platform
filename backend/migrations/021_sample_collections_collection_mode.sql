-- SUPERSEDED by 021_sample_collection_missing_columns.sql
--
-- This file is retained for path compatibility with older runbooks and docs.
-- It re-applies the same additive ADD COLUMN IF NOT EXISTS statements for
-- collection_mode and field-request metadata only (idempotent, no DROP/ALTER).
--
-- Prefer the consolidating migration for production:
--   backend/migrations/021_sample_collection_missing_columns.sql
--   python backend/scripts/apply_sample_collections_collection_mode.py

ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collection_mode VARCHAR(50);
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
