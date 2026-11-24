-- Per-clinic contracts, price lists, statements (kết toán) and payments (công nợ) — additive, idempotent. PostgreSQL.
-- organization_id = partner_organizations.id of the clinic. Core order/invoice tables are not altered.

CREATE TABLE IF NOT EXISTS clinic_billing_settings (
    organization_id VARCHAR(36) PRIMARY KEY,
    default_discount_pct DOUBLE PRECISION NOT NULL DEFAULT 0,
    payment_terms_days INTEGER NOT NULL DEFAULT 30,
    updated_by VARCHAR(120),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS clinic_contracts (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    contract_no VARCHAR(80),
    title VARCHAR(200) NOT NULL,
    signed_date VARCHAR(10),
    start_date VARCHAR(10),
    end_date VARCHAR(10),
    note VARCHAR(500),
    file_id VARCHAR(36),
    file_name VARCHAR(255),
    created_by VARCHAR(120),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_clinic_contracts_org ON clinic_contracts (organization_id);

CREATE TABLE IF NOT EXISTS clinic_prices (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    test_catalog_id VARCHAR(36) NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    updated_by VARCHAR(120),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_clinic_prices_org_test UNIQUE (organization_id, test_catalog_id)
);

CREATE TABLE IF NOT EXISTS clinic_statements (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    statement_no VARCHAR(40) NOT NULL UNIQUE,
    period_start VARCHAR(10) NOT NULL,
    period_end VARCHAR(10) NOT NULL,
    order_count INTEGER NOT NULL DEFAULT 0,
    total_amount DOUBLE PRECISION NOT NULL DEFAULT 0,
    due_date VARCHAR(10) NOT NULL,
    note VARCHAR(300),
    created_by VARCHAR(120),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_clinic_statements_org ON clinic_statements (organization_id);

CREATE TABLE IF NOT EXISTS clinic_statement_lines (
    id VARCHAR(36) PRIMARY KEY,
    statement_id VARCHAR(36) NOT NULL,
    order_code VARCHAR(50) NOT NULL UNIQUE,
    patient_name VARCHAR(255),
    amount DOUBLE PRECISION NOT NULL DEFAULT 0,
    ordered_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_clinic_statement_lines_stmt ON clinic_statement_lines (statement_id);

CREATE TABLE IF NOT EXISTS clinic_payments (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    paid_at VARCHAR(10) NOT NULL,
    method VARCHAR(40),
    reference VARCHAR(120),
    note VARCHAR(300),
    created_by VARCHAR(120),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_clinic_payments_org ON clinic_payments (organization_id);
