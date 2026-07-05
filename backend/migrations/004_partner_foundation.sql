-- Sprint 005 — Multi-Tenant Organization & Partner Foundation (additive, PostgreSQL)

CREATE TABLE IF NOT EXISTS organizations (
    id VARCHAR(36) PRIMARY KEY,
    organization_code VARCHAR(50) NOT NULL UNIQUE,
    organization_name VARCHAR(255) NOT NULL,
    organization_type VARCHAR(50) NOT NULL DEFAULT 'CLINIC',
    tax_code VARCHAR(50),
    business_license VARCHAR(100),
    address VARCHAR(500),
    phone VARCHAR(50),
    email VARCHAR(255),
    website VARCHAR(255),
    contact_person VARCHAR(255),
    status VARCHAR(30) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_organizations_type ON organizations (organization_type);
CREATE INDEX IF NOT EXISTS idx_organizations_status ON organizations (status);

CREATE TABLE IF NOT EXISTS organization_roles (
    id VARCHAR(36) PRIMARY KEY,
    role_code VARCHAR(50) NOT NULL UNIQUE,
    role_name VARCHAR(100) NOT NULL,
    permissions_json TEXT DEFAULT '[]',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organization_users (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL REFERENCES organizations(id),
    user_id VARCHAR(36) NOT NULL REFERENCES users(id),
    role_code VARCHAR(50) NOT NULL DEFAULT 'VIEWER',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    invited_by VARCHAR(255),
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (organization_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_organization_users_org ON organization_users (organization_id);
CREATE INDEX IF NOT EXISTS idx_organization_users_user ON organization_users (user_id);

CREATE TABLE IF NOT EXISTS partner_contracts (
    id VARCHAR(36) PRIMARY KEY,
    contract_code VARCHAR(50) NOT NULL UNIQUE,
    organization_id VARCHAR(36) NOT NULL REFERENCES organizations(id),
    start_date VARCHAR(20),
    end_date VARCHAR(20),
    discount_percent DOUBLE PRECISION DEFAULT 0,
    payment_terms VARCHAR(100),
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_partner_contracts_org ON partner_contracts (organization_id);

CREATE TABLE IF NOT EXISTS organization_price_lists (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL REFERENCES organizations(id),
    price_list_code VARCHAR(100) NOT NULL,
    price_tier VARCHAR(30) NOT NULL DEFAULT 'retail',
    effective_from VARCHAR(20),
    effective_to VARCHAR(20),
    is_default BOOLEAN DEFAULT FALSE,
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (organization_id, price_tier)
);
CREATE INDEX IF NOT EXISTS idx_org_price_lists_org ON organization_price_lists (organization_id);

ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);

-- Seed internal organization (idempotent)
INSERT INTO organizations (id, organization_code, organization_name, organization_type, status)
SELECT '00000000-0000-4000-8000-000000000001', 'DXCON_INTERNAL', 'DxCon Internal', 'DXCON_INTERNAL', 'active'
WHERE NOT EXISTS (SELECT 1 FROM organizations WHERE organization_code = 'DXCON_INTERNAL');

UPDATE users SET organization_id = '00000000-0000-4000-8000-000000000001'
WHERE organization_id IS NULL;
