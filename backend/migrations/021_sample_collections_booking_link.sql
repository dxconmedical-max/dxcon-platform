-- Follow-up for environments that already applied an incomplete 020 which only
-- ALTER'd later production columns inside CREATE TABLE IF NOT EXISTS for the
-- Release 0.4 booking link fields.
--
-- Production traceback addressed:
--   psycopg2.errors.UndefinedColumn:
--   column sample_collections.marketplace_booking_id does not exist
--
-- Additive + idempotent. No data rewrite.

ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS marketplace_booking_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS sample_tracking_id VARCHAR(36);

CREATE INDEX IF NOT EXISTS ix_sample_collections_marketplace_booking_id
    ON sample_collections(marketplace_booking_id);
