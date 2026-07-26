-- Sprint 008 — Reporting Engine and Doctor Review (additive, PostgreSQL)

CREATE TABLE IF NOT EXISTS clinical_reports (
    id VARCHAR(36) PRIMARY KEY,
    report_code VARCHAR(50) NOT NULL UNIQUE,
    order_id VARCHAR(36) NOT NULL,
    order_code VARCHAR(50) NOT NULL,
    patient_id VARCHAR(50) NOT NULL,
    accession_id VARCHAR(36),
    accession_number VARCHAR(50),
    organization_id VARCHAR(36),
    laboratory_id VARCHAR(36),
    result_id VARCHAR(36),
    report_status VARCHAR(30) NOT NULL DEFAULT 'draft',
    report_version INTEGER NOT NULL DEFAULT 1,
    report_type VARCHAR(30) DEFAULT 'diagnostic',
    generated_at TIMESTAMP,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    released_by VARCHAR(255),
    released_at TIMESTAMP,
    doctor_note TEXT,
    lab_note TEXT,
    clinical_summary TEXT,
    pdf_path VARCHAR(500),
    report_hash VARCHAR(128),
    qr_payload VARCHAR(255),
    html_content TEXT,
    is_visible_to_patient BOOLEAN DEFAULT FALSE,
    amended_from_report_id VARCHAR(36),
    amendment_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_clinical_reports_order ON clinical_reports (order_code);
CREATE INDEX IF NOT EXISTS idx_clinical_reports_patient ON clinical_reports (patient_id);
CREATE INDEX IF NOT EXISTS idx_clinical_reports_status ON clinical_reports (report_status);

CREATE TABLE IF NOT EXISTS report_digital_signatures (
    id VARCHAR(36) PRIMARY KEY,
    report_id VARCHAR(36) NOT NULL REFERENCES clinical_reports(id),
    signer_id VARCHAR(36),
    signer_name VARCHAR(255),
    signer_role VARCHAR(50),
    signed_at TIMESTAMP,
    signature_hash VARCHAR(128),
    report_hash VARCHAR(128),
    signature_method VARCHAR(50) DEFAULT 'INTERNAL_APPROVAL',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS critical_result_alerts (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(36),
    order_code VARCHAR(50),
    result_id VARCHAR(36),
    report_id VARCHAR(36),
    critical_type VARCHAR(50),
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP,
    status VARCHAR(30) DEFAULT 'new',
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_critical_alerts_status ON critical_result_alerts (status);

CREATE TABLE IF NOT EXISTS report_notification_events (
    id VARCHAR(36) PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    recipient_type VARCHAR(30),
    recipient_id VARCHAR(50),
    channel VARCHAR(30),
    status VARCHAR(30) DEFAULT 'pending',
    payload_json TEXT,
    report_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
