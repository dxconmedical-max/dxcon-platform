-- Sprint 007 — Laboratory Workspace + LIS Integration Foundation (additive, PostgreSQL)

ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS condition_status VARCHAR(30);
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS receive_note TEXT;

ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS workflow_status VARCHAR(30) DEFAULT 'draft';
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS result_source VARCHAR(30) DEFAULT 'manual';
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS import_batch_id VARCHAR(36);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS instrument VARCHAR(100);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS technician VARCHAR(255);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS result_time TIMESTAMP;
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS entry_note TEXT;

CREATE TABLE IF NOT EXISTS lab_accession_records (
    id VARCHAR(36) PRIMARY KEY,
    accession_number VARCHAR(50) NOT NULL UNIQUE,
    order_id VARCHAR(36) NOT NULL,
    order_code VARCHAR(50) NOT NULL,
    sample_code VARCHAR(50),
    patient_code VARCHAR(50),
    accessioned_by VARCHAR(255),
    accessioned_at TIMESTAMP,
    laboratory_id VARCHAR(36),
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_lab_accession_order ON lab_accession_records (order_code);
CREATE INDEX IF NOT EXISTS idx_lab_accession_sample ON lab_accession_records (sample_code);

CREATE TABLE IF NOT EXISTS lis_connectors (
    id VARCHAR(36) PRIMARY KEY,
    connector_code VARCHAR(50) NOT NULL UNIQUE,
    connector_name VARCHAR(255) NOT NULL,
    connector_type VARCHAR(30) NOT NULL DEFAULT 'MANUAL',
    organization_id VARCHAR(36),
    laboratory_id VARCHAR(36),
    base_url VARCHAR(500),
    auth_type VARCHAR(30),
    username VARCHAR(255),
    api_key_reference VARCHAR(255),
    sftp_host VARCHAR(255),
    sftp_path VARCHAR(500),
    status VARCHAR(30) DEFAULT 'active',
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lis_field_mappings (
    id VARCHAR(36) PRIMARY KEY,
    connector_id VARCHAR(36) NOT NULL REFERENCES lis_connectors(id),
    external_field VARCHAR(100) NOT NULL,
    dxcon_field VARCHAR(100) NOT NULL,
    transform_rule VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (connector_id, external_field)
);

CREATE TABLE IF NOT EXISTS lis_import_batches (
    id VARCHAR(36) PRIMARY KEY,
    batch_code VARCHAR(50) NOT NULL UNIQUE,
    connector_id VARCHAR(36) REFERENCES lis_connectors(id),
    import_type VARCHAR(30) NOT NULL,
    file_name VARCHAR(255),
    status VARCHAR(30) DEFAULT 'processing',
    total_rows INTEGER DEFAULT 0,
    success_rows INTEGER DEFAULT 0,
    failed_rows INTEGER DEFAULT 0,
    imported_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lis_import_failed_rows (
    id VARCHAR(36) PRIMARY KEY,
    batch_id VARCHAR(36) NOT NULL REFERENCES lis_import_batches(id),
    connector_id VARCHAR(36),
    row_number INTEGER,
    error_reason TEXT NOT NULL,
    raw_payload TEXT,
    status VARCHAR(30) DEFAULT 'failed',
    retried_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_lis_failed_batch ON lis_import_failed_rows (batch_id);
