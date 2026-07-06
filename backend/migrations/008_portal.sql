-- Sprint 009 — Doctor Portal and Patient Portal (additive, PostgreSQL)

CREATE TABLE IF NOT EXISTS portal_notifications (
    id VARCHAR(36) PRIMARY KEY,
    recipient_type VARCHAR(30) NOT NULL,
    recipient_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    channel VARCHAR(30) DEFAULT 'IN_APP',
    title VARCHAR(255),
    body TEXT,
    status VARCHAR(30) DEFAULT 'unread',
    payload_json TEXT,
    read_at TIMESTAMP,
    organization_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_portal_notifications_recipient ON portal_notifications (recipient_type, recipient_id);
CREATE INDEX IF NOT EXISTS idx_portal_notifications_status ON portal_notifications (status);

CREATE TABLE IF NOT EXISTS portal_qr_tokens (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    verification_token VARCHAR(128) NOT NULL UNIQUE,
    organization_id VARCHAR(36),
    qr_payload VARCHAR(255),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_portal_qr_patient ON portal_qr_tokens (patient_id);

ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS note_type VARCHAR(50) DEFAULT 'clinical';
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS visibility VARCHAR(30) DEFAULT 'internal';
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS order_code VARCHAR(50);
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS report_code VARCHAR(50);
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS follow_up_recommendation TEXT;
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

CREATE TABLE IF NOT EXISTS portal_favorites (
    id VARCHAR(36) PRIMARY KEY,
    owner_type VARCHAR(20) NOT NULL,
    owner_id VARCHAR(50) NOT NULL,
    favorite_type VARCHAR(30) NOT NULL,
    favorite_id VARCHAR(50) NOT NULL,
    label VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_portal_favorites_owner ON portal_favorites (owner_type, owner_id);
