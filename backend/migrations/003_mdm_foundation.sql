-- MDM Foundation — additive, idempotent (PostgreSQL)

CREATE TABLE IF NOT EXISTS mdm_import_batches (
    id VARCHAR(36) PRIMARY KEY,
    batch_code VARCHAR(50) UNIQUE NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    file_name VARCHAR(255),
    file_format VARCHAR(20),
    total_rows INTEGER DEFAULT 0,
    valid_rows INTEGER DEFAULT 0,
    duplicate_rows INTEGER DEFAULT 0,
    error_rows INTEGER DEFAULT 0,
    committed_rows INTEGER DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    preview_json TEXT DEFAULT '{}',
    error_summary TEXT,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    committed_by VARCHAR(255),
    committed_at TIMESTAMP,
    rolled_back_by VARCHAR(255),
    rolled_back_at TIMESTAMP,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mdm_import_batches_entity ON mdm_import_batches(entity_type);
CREATE INDEX IF NOT EXISTS idx_mdm_import_batches_status ON mdm_import_batches(status);

CREATE TABLE IF NOT EXISTS mdm_master_records (
    id VARCHAR(36) PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    code VARCHAR(100) NOT NULL,
    name VARCHAR(500) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    attributes_json TEXT DEFAULT '{}',
    parent_code VARCHAR(100),
    tenant_id VARCHAR(36),
    source VARCHAR(50) DEFAULT 'mdm',
    external_id VARCHAR(100),
    import_batch_id VARCHAR(36) REFERENCES mdm_import_batches(id),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_mdm_entity_code UNIQUE (entity_type, code)
);

CREATE INDEX IF NOT EXISTS idx_mdm_master_entity ON mdm_master_records(entity_type);
CREATE INDEX IF NOT EXISTS idx_mdm_master_code ON mdm_master_records(code);
CREATE INDEX IF NOT EXISTS idx_mdm_master_status ON mdm_master_records(status);

CREATE TABLE IF NOT EXISTS mdm_import_rows (
    id VARCHAR(36) PRIMARY KEY,
    batch_id VARCHAR(36) NOT NULL REFERENCES mdm_import_batches(id),
    row_number INTEGER NOT NULL,
    code VARCHAR(100),
    name VARCHAR(500),
    status VARCHAR(20) NOT NULL DEFAULT 'valid',
    payload_json TEXT DEFAULT '{}',
    validation_errors TEXT,
    master_record_id VARCHAR(36) REFERENCES mdm_master_records(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mdm_import_rows_batch ON mdm_import_rows(batch_id);
