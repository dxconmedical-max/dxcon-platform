-- Clinic self-service order requests (phiếu chỉ định) + per-clinic enable switch — additive, idempotent. PostgreSQL.

CREATE TABLE IF NOT EXISTS clinic_order_requests (
    id VARCHAR(36) PRIMARY KEY,
    reference VARCHAR(24) NOT NULL UNIQUE,
    organization_id VARCHAR(36) NOT NULL,
    requested_by VARCHAR(120),
    patient_name VARCHAR(120) NOT NULL,
    birth_year INTEGER NOT NULL,
    tests_json TEXT NOT NULL,
    tube_count INTEGER NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'NEW',
    order_code VARCHAR(50),
    reject_reason VARCHAR(300),
    handled_by VARCHAR(120),
    handled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_clinic_order_requests_org ON clinic_order_requests (organization_id);
CREATE INDEX IF NOT EXISTS ix_clinic_order_requests_status ON clinic_order_requests (status);
CREATE INDEX IF NOT EXISTS ix_clinic_order_requests_created ON clinic_order_requests (created_at);

CREATE TABLE IF NOT EXISTS clinic_order_settings (
    organization_id VARCHAR(36) PRIMARY KEY,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    updated_by VARCHAR(120),
    updated_at TIMESTAMP DEFAULT NOW()
);
