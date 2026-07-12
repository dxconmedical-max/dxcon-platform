-- Release 8.0 Sprint 6 — Clinical Workflow and Result Governance (additive)

ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS specimen_id VARCHAR(36);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS order_item_id VARCHAR(36);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS original_value TEXT;
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS normalized_value TEXT;
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS critical_flag BOOLEAN DEFAULT FALSE;
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS analyzer_flags_json TEXT;
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS result_status VARCHAR(30) DEFAULT 'PENDING';
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS technician_reviewer VARCHAR(255);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS doctor_approver VARCHAR(255);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP;
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS amendment_of VARCHAR(36);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS audit_reference VARCHAR(64);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS preliminary_result_id VARCHAR(36);

CREATE TABLE IF NOT EXISTS clinical_workflow_transitions (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    aggregate_type VARCHAR(50) NOT NULL,
    aggregate_id VARCHAR(36) NOT NULL,
    from_status VARCHAR(50),
    to_status VARCHAR(50) NOT NULL,
    actor VARCHAR(255) NOT NULL,
    reason TEXT,
    correlation_id VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clinical_wf_org ON clinical_workflow_transitions(organization_id);
CREATE INDEX IF NOT EXISTS idx_clinical_wf_aggregate ON clinical_workflow_transitions(aggregate_type, aggregate_id);

CREATE TABLE IF NOT EXISTS critical_value_policies (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    policy_code VARCHAR(50) NOT NULL UNIQUE,
    test_code VARCHAR(50),
    analyte VARCHAR(100),
    lower_threshold DOUBLE PRECISION,
    upper_threshold DOUBLE PRECISION,
    sex VARCHAR(10),
    age_min INTEGER,
    age_max INTEGER,
    notification_recipients_json TEXT,
    acknowledgement_sla_minutes INTEGER DEFAULT 60,
    escalation_schedule_json TEXT,
    version INTEGER DEFAULT 1,
    approved_by VARCHAR(255),
    effective_at TIMESTAMP,
    status VARCHAR(30) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS report_verification_tokens (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    report_id VARCHAR(36) NOT NULL,
    report_code VARCHAR(50) NOT NULL,
    token VARCHAR(128) NOT NULL UNIQUE,
    report_version INTEGER NOT NULL,
    report_hash VARCHAR(128),
    status VARCHAR(30) DEFAULT 'ACTIVE',
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    revoked_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_report_verify_token ON report_verification_tokens(token);

CREATE TABLE IF NOT EXISTS critical_value_acknowledgements (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    alert_id VARCHAR(36),
    result_item_id VARCHAR(36),
    acknowledged_by VARCHAR(255) NOT NULL,
    acknowledged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    communication_method VARCHAR(30) DEFAULT 'in_app',
    escalation_level INTEGER DEFAULT 0,
    resolution_note TEXT,
    correlation_id VARCHAR(64)
);
