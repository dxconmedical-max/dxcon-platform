-- Epic 7 Mobile MVP (non-destructive)

CREATE TABLE IF NOT EXISTS mobile_devices (
    id VARCHAR(36) PRIMARY KEY,
    device_reference VARCHAR(80) UNIQUE NOT NULL,
    user_id VARCHAR(36) NOT NULL,
    organization_id VARCHAR(36),
    platform VARCHAR(20) NOT NULL,
    app_version VARCHAR(30),
    notification_token_hash VARCHAR(64),
    workspace VARCHAR(30),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    last_seen_at TIMESTAMP,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mobile_devices_user ON mobile_devices(user_id);
CREATE INDEX IF NOT EXISTS idx_mobile_devices_org ON mobile_devices(organization_id);

CREATE TABLE IF NOT EXISTS mobile_audit_events (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36),
    user_id VARCHAR(36),
    workspace VARCHAR(30),
    event_type VARCHAR(80) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(36),
    outcome VARCHAR(30) DEFAULT 'SUCCESS',
    correlation_id VARCHAR(80),
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mobile_audit_user ON mobile_audit_events(user_id);
CREATE INDEX IF NOT EXISTS idx_mobile_audit_org ON mobile_audit_events(organization_id);
