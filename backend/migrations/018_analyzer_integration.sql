-- Release 7.0 Sprint 5 — Analyzer Integration Foundation (additive)

ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS laboratory_id VARCHAR(36);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS vendor VARCHAR(100);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS serial_number VARCHAR(100);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS protocol VARCHAR(30) DEFAULT 'SIMULATOR';
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS connection_mode VARCHAR(30);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS host VARCHAR(255);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS port INTEGER;
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP;
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS firmware_version VARCHAR(50);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS software_version VARCHAR(50);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS calibration_status VARCHAR(30);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS maintenance_status VARCHAR(30);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS result_mode VARCHAR(30) DEFAULT 'PRELIMINARY';
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT TRUE;

CREATE TABLE IF NOT EXISTS analyzer_integration_messages (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    laboratory_id VARCHAR(36),
    analyzer_id VARCHAR(36),
    message_type VARCHAR(30) NOT NULL,
    protocol VARCHAR(30),
    status VARCHAR(30) DEFAULT 'RECEIVED',
    message_hash VARCHAR(64) NOT NULL,
    correlation_id VARCHAR(64),
    external_message_id VARCHAR(128),
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    validation_status VARCHAR(30),
    error_code VARCHAR(50),
    payload_ref VARCHAR(255),
    redacted_summary TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_analyzer_integration_messages_hash ON analyzer_integration_messages(message_hash);
CREATE INDEX IF NOT EXISTS idx_analyzer_integration_messages_org ON analyzer_integration_messages(organization_id);

CREATE TABLE IF NOT EXISTS integration_test_mappings (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    mapping_code VARCHAR(50) NOT NULL UNIQUE,
    analyzer_test_code VARCHAR(50) NOT NULL,
    dxcon_test_code VARCHAR(50) NOT NULL,
    specimen_type VARCHAR(50),
    unit VARCHAR(30),
    decimal_precision INTEGER DEFAULT 2,
    loinc_code VARCHAR(20),
    version INTEGER DEFAULT 1,
    approved_by VARCHAR(255),
    effective_at TIMESTAMP,
    status VARCHAR(30) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS integration_quarantine (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    message_id VARCHAR(36) REFERENCES analyzer_integration_messages(id),
    reason_code VARCHAR(50) NOT NULL,
    reason_detail TEXT,
    specimen_barcode VARCHAR(50),
    analyzer_test_code VARCHAR(50),
    original_value TEXT,
    normalized_value TEXT,
    status VARCHAR(30) DEFAULT 'OPEN',
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analyzer_worklist_items (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    analyzer_id VARCHAR(36) NOT NULL,
    specimen_barcode VARCHAR(50),
    order_code VARCHAR(50),
    test_code VARCHAR(50),
    status VARCHAR(30) DEFAULT 'QUEUED',
    sent_at TIMESTAMP,
    acknowledged_at TIMESTAMP,
    completed_at TIMESTAMP,
    correlation_id VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analyzer_preliminary_results (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    analyzer_id VARCHAR(36),
    message_id VARCHAR(36) REFERENCES analyzer_integration_messages(id),
    specimen_barcode VARCHAR(50),
    order_code VARCHAR(50),
    test_code VARCHAR(50),
    original_value TEXT NOT NULL,
    normalized_value TEXT,
    unit VARCHAR(30),
    flag VARCHAR(30),
    review_status VARCHAR(30) DEFAULT 'PENDING_REVIEW',
    auto_released BOOLEAN DEFAULT FALSE,
    duplicate_of VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_prelim_results_org ON analyzer_preliminary_results(organization_id);
CREATE INDEX IF NOT EXISTS idx_prelim_results_barcode ON analyzer_preliminary_results(specimen_barcode);
