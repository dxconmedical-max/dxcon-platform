-- Release 1.0 — Operations Center (additive, PostgreSQL)

CREATE TABLE IF NOT EXISTS opsc_support_tickets (
    id VARCHAR(36) PRIMARY KEY,
    ticket_code VARCHAR(50) UNIQUE NOT NULL,
    organization_id VARCHAR(36),
    subject VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'GENERAL',
    priority VARCHAR(30) DEFAULT 'NORMAL',
    status VARCHAR(50) DEFAULT 'OPEN',
    requester_email VARCHAR(255),
    assigned_to VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_opsc_support_tickets_status ON opsc_support_tickets (status);
CREATE INDEX IF NOT EXISTS ix_opsc_support_tickets_organization_id ON opsc_support_tickets (organization_id);

CREATE TABLE IF NOT EXISTS opsc_customer_requests (
    id VARCHAR(36) PRIMARY KEY,
    request_code VARCHAR(50) UNIQUE NOT NULL,
    organization_id VARCHAR(36),
    request_type VARCHAR(50) DEFAULT 'FEATURE',
    title VARCHAR(255) NOT NULL,
    details TEXT,
    status VARCHAR(50) DEFAULT 'PENDING',
    priority VARCHAR(30) DEFAULT 'NORMAL',
    requested_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS ix_opsc_customer_requests_status ON opsc_customer_requests (status);
CREATE INDEX IF NOT EXISTS ix_opsc_customer_requests_organization_id ON opsc_customer_requests (organization_id);
