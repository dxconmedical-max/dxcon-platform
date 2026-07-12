-- Release 7.0 — LIMS Core (additive, PostgreSQL)

CREATE TABLE IF NOT EXISTS specimens (
    id VARCHAR(36) PRIMARY KEY,
    barcode VARCHAR(50) NOT NULL UNIQUE,
    human_readable VARCHAR(50) NOT NULL UNIQUE,
    order_id VARCHAR(36),
    order_code VARCHAR(50),
    patient_code VARCHAR(50),
    organization_id VARCHAR(36),
    status VARCHAR(30) NOT NULL DEFAULT 'CREATED',
    container_type VARCHAR(30),
    volume DOUBLE PRECISION,
    volume_unit VARCHAR(20) DEFAULT 'mL',
    collected_at TIMESTAMP,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_specimens_order_code ON specimens (order_code);
CREATE INDEX IF NOT EXISTS idx_specimens_status ON specimens (status);
CREATE INDEX IF NOT EXISTS idx_specimens_org ON specimens (organization_id);

CREATE TABLE IF NOT EXISTS containers (
    id VARCHAR(36) PRIMARY KEY,
    container_code VARCHAR(50) NOT NULL UNIQUE,
    container_type VARCHAR(30) NOT NULL,
    volume_capacity DOUBLE PRECISION,
    volume_unit VARCHAR(20) DEFAULT 'mL',
    specimen_id VARCHAR(36) REFERENCES specimens(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_containers_specimen ON containers (specimen_id);

CREATE TABLE IF NOT EXISTS barcode_logs (
    id VARCHAR(36) PRIMARY KEY,
    barcode_value VARCHAR(100) NOT NULL UNIQUE,
    human_readable VARCHAR(50) NOT NULL,
    format VARCHAR(20) NOT NULL DEFAULT 'CODE128',
    specimen_id VARCHAR(36) REFERENCES specimens(id),
    generated_by VARCHAR(255),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_barcode_logs_specimen ON barcode_logs (specimen_id);
CREATE INDEX IF NOT EXISTS idx_barcode_logs_human ON barcode_logs (human_readable);

CREATE TABLE IF NOT EXISTS storage_locations (
    id VARCHAR(36) PRIMARY KEY,
    location_code VARCHAR(50) NOT NULL UNIQUE,
    rack VARCHAR(50),
    shelf VARCHAR(50),
    batch VARCHAR(50),
    laboratory_id VARCHAR(36),
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS accessions (
    id VARCHAR(36) PRIMARY KEY,
    accession_number VARCHAR(50) NOT NULL UNIQUE,
    specimen_id VARCHAR(36) NOT NULL REFERENCES specimens(id),
    storage_location_id VARCHAR(36) REFERENCES storage_locations(id),
    rack VARCHAR(50),
    shelf VARCHAR(50),
    batch VARCHAR(50),
    operator VARCHAR(255),
    accessioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(30) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_accessions_specimen ON accessions (specimen_id);

CREATE TABLE IF NOT EXISTS sample_status_history (
    id VARCHAR(36) PRIMARY KEY,
    specimen_id VARCHAR(36) NOT NULL REFERENCES specimens(id),
    from_status VARCHAR(30),
    to_status VARCHAR(30) NOT NULL,
    actor VARCHAR(255),
    note TEXT,
    transitioned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sample_status_history_specimen ON sample_status_history (specimen_id);
CREATE INDEX IF NOT EXISTS idx_sample_status_history_at ON sample_status_history (transitioned_at);
