-- Full birth date on clinic order requests (optional; birth_year stays required) — additive, idempotent. PostgreSQL.
ALTER TABLE clinic_order_requests ADD COLUMN IF NOT EXISTS birth_date VARCHAR(10);
