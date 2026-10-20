-- Report logos (DxCon, laboratory, partner, client) — additive, idempotent.
-- PostgreSQL only.

CREATE TABLE IF NOT EXISTS report_logos (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id),
    owner_type VARCHAR(30) NOT NULL,
    owner_code VARCHAR(100) NOT NULL DEFAULT '',
    display_name VARCHAR(255) NOT NULL,
    storage_key VARCHAR(500) NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    size_bytes INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_report_logos_owner ON report_logos (owner_type, owner_code);
