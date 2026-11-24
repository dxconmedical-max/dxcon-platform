-- Lab cost prices (giá nhập), order→lab assignment with margin, and payables to labs (công nợ phải trả) — additive, idempotent. PostgreSQL.
-- organization_id = organizations.id of the performing lab. Core order/invoice tables are not altered.

CREATE TABLE IF NOT EXISTS lab_partners (
    organization_id VARCHAR(36) PRIMARY KEY,
    created_by VARCHAR(120),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lab_cost_prices (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    test_catalog_id VARCHAR(36) NOT NULL,
    cost DOUBLE PRECISION NOT NULL,
    updated_by VARCHAR(120),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_lab_cost_prices_org_test UNIQUE (organization_id, test_catalog_id)
);

-- scope_org_id = a clinic's organization id, or 'DEFAULT' for the lab used when nothing else is specified.
CREATE TABLE IF NOT EXISTS lab_routing (
    scope_org_id VARCHAR(36) PRIMARY KEY,
    lab_organization_id VARCHAR(36) NOT NULL,
    updated_by VARCHAR(120),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS order_lab_costs (
    id VARCHAR(36) PRIMARY KEY,
    order_code VARCHAR(50) NOT NULL UNIQUE,
    lab_organization_id VARCHAR(36) NOT NULL,
    cost_total DOUBLE PRECISION NOT NULL DEFAULT 0,
    sell_total DOUBLE PRECISION NOT NULL DEFAULT 0,
    missing_count INTEGER NOT NULL DEFAULT 0,
    assigned_by VARCHAR(120),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_order_lab_costs_lab ON order_lab_costs (lab_organization_id);

CREATE TABLE IF NOT EXISTS lab_payable_statements (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    statement_no VARCHAR(40) NOT NULL UNIQUE,
    period_start VARCHAR(10) NOT NULL,
    period_end VARCHAR(10) NOT NULL,
    order_count INTEGER NOT NULL DEFAULT 0,
    total_amount DOUBLE PRECISION NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    note VARCHAR(300),
    created_by VARCHAR(120),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_lab_payable_statements_org ON lab_payable_statements (organization_id);

CREATE TABLE IF NOT EXISTS lab_payable_lines (
    id VARCHAR(36) PRIMARY KEY,
    statement_id VARCHAR(36) NOT NULL,
    order_code VARCHAR(50) NOT NULL UNIQUE,
    amount DOUBLE PRECISION NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS ix_lab_payable_lines_stmt ON lab_payable_lines (statement_id);

CREATE TABLE IF NOT EXISTS lab_payments (
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
CREATE INDEX IF NOT EXISTS ix_lab_payments_org ON lab_payments (organization_id);
