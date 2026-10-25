-- Tenant scope columns for patients and biz_orders — additive, idempotent.
-- PostgreSQL only. Existing rows stay NULL (platform-level / demo data).

ALTER TABLE patients ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);

CREATE INDEX IF NOT EXISTS ix_patients_organization_id ON patients (organization_id);
CREATE INDEX IF NOT EXISTS ix_biz_orders_organization_id ON biz_orders (organization_id);
