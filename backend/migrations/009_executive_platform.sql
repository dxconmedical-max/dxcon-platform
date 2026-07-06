-- Sprint 010 — Executive Platform and Production Readiness (additive, PostgreSQL)

CREATE TABLE IF NOT EXISTS launch_checklist_items (
    id VARCHAR(36) PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    item_key VARCHAR(100) NOT NULL UNIQUE,
    label VARCHAR(255) NOT NULL,
    status VARCHAR(30) DEFAULT 'pending',
    verified_at TIMESTAMP,
    verified_by VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pilot_wizard_sessions (
    id VARCHAR(36) PRIMARY KEY,
    organization_name VARCHAR(255),
    current_step VARCHAR(50) DEFAULT 'organization',
    checklist_json TEXT,
    status VARCHAR(30) DEFAULT 'in_progress',
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS storage_config (
    id VARCHAR(36) PRIMARY KEY,
    provider VARCHAR(30) DEFAULT 'local',
    bucket_name VARCHAR(255),
    base_path VARCHAR(500),
    is_active BOOLEAN DEFAULT TRUE,
    config_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
