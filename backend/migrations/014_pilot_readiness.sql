-- Release 2.0 Epic 8 — Pilot readiness (additive, non-destructive)

CREATE TABLE IF NOT EXISTS pilot_onboarding_sessions (
    id VARCHAR(36) PRIMARY KEY,
    session_code VARCHAR(50) UNIQUE NOT NULL,
    onboarding_type VARCHAR(50) NOT NULL,
    current_step VARCHAR(50) DEFAULT 'organization',
    status VARCHAR(50) DEFAULT 'IN_PROGRESS',
    organization_id VARCHAR(36),
    payload_json TEXT,
    requester_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pilot_onb_org ON pilot_onboarding_sessions(organization_id);

CREATE TABLE IF NOT EXISTS pilot_partner_registrations (
    id VARCHAR(36) PRIMARY KEY,
    registration_code VARCHAR(50) UNIQUE NOT NULL,
    partner_type VARCHAR(50) NOT NULL,
    organization_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(30),
    domain VARCHAR(255),
    address TEXT,
    status VARCHAR(50) DEFAULT 'PENDING',
    organization_id VARCHAR(36),
    review_note TEXT,
    reviewed_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pilot_reg_status ON pilot_partner_registrations(status);

CREATE TABLE IF NOT EXISTS pilot_org_setup_sessions (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36) NOT NULL,
    current_step VARCHAR(50) DEFAULT 'organization',
    status VARCHAR(50) DEFAULT 'IN_PROGRESS',
    payload_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pilot_org_setup ON pilot_org_setup_sessions(organization_id);

CREATE TABLE IF NOT EXISTS pilot_knowledge_articles (
    id VARCHAR(36) PRIMARY KEY,
    article_code VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(50) DEFAULT 'FAQ',
    title VARCHAR(255) NOT NULL,
    body TEXT,
    content_type VARCHAR(30) DEFAULT 'ARTICLE',
    tags VARCHAR(500),
    published BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pilot_training_guides (
    id VARCHAR(36) PRIMARY KEY,
    guide_code VARCHAR(50) UNIQUE NOT NULL,
    audience VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    sort_order INTEGER DEFAULT 0,
    published BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pilot_scorecard_runs (
    id VARCHAR(36) PRIMARY KEY,
    run_code VARCHAR(50) UNIQUE NOT NULL,
    score_pct FLOAT DEFAULT 0,
    metrics_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
