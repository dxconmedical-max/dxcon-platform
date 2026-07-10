-- Epic 3.5 Integration & Interoperability Foundation (non-destructive)

CREATE TABLE IF NOT EXISTS intg_connectors (
    id VARCHAR(36) PRIMARY KEY,
    connector_code VARCHAR(80) UNIQUE NOT NULL,
    connector_name VARCHAR(255) NOT NULL,
    connector_type VARCHAR(30) NOT NULL,
    vendor VARCHAR(100),
    protocol VARCHAR(30) NOT NULL,
    organization_id VARCHAR(36) NOT NULL,
    laboratory_id VARCHAR(36),
    clinic_id VARCHAR(36),
    base_url VARCHAR(500),
    direction VARCHAR(20) NOT NULL DEFAULT 'INBOUND',
    authentication_type VARCHAR(30),
    secret_reference VARCHAR(255),
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
    environment VARCHAR(20) DEFAULT 'production',
    lis_connector_id VARCHAR(36),
    last_success_at TIMESTAMP,
    last_failure_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_intg_connectors_org ON intg_connectors(organization_id);
CREATE INDEX IF NOT EXISTS idx_intg_connectors_status ON intg_connectors(status);

CREATE TABLE IF NOT EXISTS intg_messages (
    id VARCHAR(36) PRIMARY KEY,
    message_id VARCHAR(80) UNIQUE NOT NULL,
    connector_id VARCHAR(36) NOT NULL,
    organization_id VARCHAR(36) NOT NULL,
    direction VARCHAR(20) NOT NULL,
    message_type VARCHAR(50) NOT NULL,
    external_message_id VARCHAR(255),
    correlation_id VARCHAR(255),
    payload_format VARCHAR(20),
    payload_hash VARCHAR(64),
    status VARCHAR(30) NOT NULL DEFAULT 'RECEIVED',
    received_at TIMESTAMP,
    processed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    error_code VARCHAR(50),
    error_message TEXT,
    payload_preview TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(connector_id, external_message_id, message_type)
);

CREATE INDEX IF NOT EXISTS idx_intg_messages_org ON intg_messages(organization_id);
CREATE INDEX IF NOT EXISTS idx_intg_messages_status ON intg_messages(status);

CREATE TABLE IF NOT EXISTS intg_mapping_rules (
    id VARCHAR(36) PRIMARY KEY,
    connector_id VARCHAR(36) NOT NULL,
    organization_id VARCHAR(36) NOT NULL,
    external_field VARCHAR(100) NOT NULL,
    canonical_field VARCHAR(100) NOT NULL,
    transformation_type VARCHAR(30) DEFAULT 'DIRECT',
    default_value VARCHAR(255),
    required BOOLEAN DEFAULT FALSE,
    value_mapping_json TEXT,
    date_format VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intg_external_mappings (
    id VARCHAR(36) PRIMARY KEY,
    connector_id VARCHAR(36) NOT NULL,
    organization_id VARCHAR(36) NOT NULL,
    mapping_kind VARCHAR(30) NOT NULL,
    external_code VARCHAR(100) NOT NULL,
    internal_code VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(connector_id, mapping_kind, external_code)
);

CREATE TABLE IF NOT EXISTS intg_webhook_subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    connector_id VARCHAR(36),
    event_type VARCHAR(80) NOT NULL,
    endpoint_url VARCHAR(500) NOT NULL,
    secret_reference VARCHAR(255),
    status VARCHAR(20) DEFAULT 'ACTIVE',
    retry_policy VARCHAR(30) DEFAULT 'EXPONENTIAL_BACKOFF',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intg_delivery_attempts (
    id VARCHAR(36) PRIMARY KEY,
    subscription_id VARCHAR(36) NOT NULL,
    organization_id VARCHAR(36) NOT NULL,
    delivery_id VARCHAR(80) UNIQUE NOT NULL,
    event_type VARCHAR(80) NOT NULL,
    payload_hash VARCHAR(64),
    status VARCHAR(20) NOT NULL,
    attempt_number INTEGER DEFAULT 1,
    next_retry_at TIMESTAMP,
    last_error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intg_api_credentials (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    name VARCHAR(100) NOT NULL,
    credential_type VARCHAR(30) NOT NULL,
    key_hash VARCHAR(128) NOT NULL,
    secret_reference VARCHAR(255),
    scopes_json TEXT DEFAULT '[]',
    ip_allowlist_json TEXT,
    expires_at TIMESTAMP,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intg_dead_letters (
    id VARCHAR(36) PRIMARY KEY,
    message_id VARCHAR(36) NOT NULL,
    organization_id VARCHAR(36) NOT NULL,
    connector_id VARCHAR(36) NOT NULL,
    retry_count INTEGER DEFAULT 0,
    maximum_retries INTEGER DEFAULT 5,
    last_error TEXT,
    retry_strategy VARCHAR(30) DEFAULT 'EXPONENTIAL_BACKOFF',
    next_retry_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'DEAD_LETTER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS intg_audit_events (
    id VARCHAR(36) PRIMARY KEY,
    action VARCHAR(80) NOT NULL,
    actor VARCHAR(255),
    organization_id VARCHAR(36),
    connector_id VARCHAR(36),
    message_id VARCHAR(36),
    correlation_id VARCHAR(255),
    outcome VARCHAR(20),
    detail_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
