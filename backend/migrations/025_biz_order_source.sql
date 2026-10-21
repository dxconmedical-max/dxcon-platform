-- Order source (referring clinic / walk-in) for statistics and report branding — additive, idempotent.
-- PostgreSQL only.

ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS source_type VARCHAR(30);
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS source_org_code VARCHAR(100);
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS source_org_name_raw VARCHAR(255);
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS external_ref VARCHAR(100);
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS attributes TEXT;

CREATE INDEX IF NOT EXISTS ix_biz_orders_source_org_code ON biz_orders (source_org_code);
