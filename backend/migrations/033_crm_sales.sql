-- CRM: customer accounts owned by sales staff, contact log, monthly sales targets — additive, idempotent. PostgreSQL.
-- organization_id links an account to a real partner organization so actual orders can be compared with the estimate.

CREATE TABLE IF NOT EXISTS crm_accounts (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    account_type VARCHAR(20) NOT NULL DEFAULT 'CLINIC',
    organization_id VARCHAR(36) UNIQUE,
    stage VARCHAR(20) NOT NULL DEFAULT 'LEAD',
    owner_user_id VARCHAR(36),
    owner_name VARCHAR(120),
    contact_person VARCHAR(120),
    phone VARCHAR(40),
    address VARCHAR(300),
    district VARCHAR(80),
    est_monthly_cases INTEGER NOT NULL DEFAULT 0,
    next_followup_date VARCHAR(10),
    notes VARCHAR(1000),
    last_activity_at TIMESTAMP,
    created_by VARCHAR(120),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_crm_accounts_owner ON crm_accounts (owner_user_id);
CREATE INDEX IF NOT EXISTS ix_crm_accounts_stage ON crm_accounts (stage);

CREATE TABLE IF NOT EXISTS crm_activities (
    id VARCHAR(36) PRIMARY KEY,
    account_id VARCHAR(36) NOT NULL,
    kind VARCHAR(20) NOT NULL DEFAULT 'NOTE',
    summary VARCHAR(1000) NOT NULL,
    created_by_user_id VARCHAR(36),
    created_by_name VARCHAR(120),
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS ix_crm_activities_account ON crm_activities (account_id);

CREATE TABLE IF NOT EXISTS crm_sale_targets (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    month VARCHAR(7) NOT NULL,
    target_cases INTEGER NOT NULL DEFAULT 0,
    target_revenue DOUBLE PRECISION NOT NULL DEFAULT 0,
    updated_by VARCHAR(120),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT uq_crm_sale_targets_user_month UNIQUE (user_id, month)
);
