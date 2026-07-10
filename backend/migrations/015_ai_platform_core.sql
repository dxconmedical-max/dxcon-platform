-- Release 3.0 Epic 9 — AI Platform Core (additive)

CREATE TABLE IF NOT EXISTS ai_platform_providers (
    id VARCHAR(36) PRIMARY KEY,
    provider_code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    provider_type VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) DEFAULT 'local-advisory',
    config_json TEXT DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_platform_prompts (
    id VARCHAR(36) PRIMARY KEY,
    prompt_code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    task_type VARCHAR(100) NOT NULL,
    active_version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_platform_prompt_versions (
    id VARCHAR(36) PRIMARY KEY,
    prompt_id VARCHAR(36) NOT NULL,
    version INTEGER NOT NULL,
    template_text TEXT NOT NULL,
    metadata_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_platform_inference_jobs (
    id VARCHAR(36) PRIMARY KEY,
    job_code VARCHAR(50) UNIQUE NOT NULL,
    organization_id VARCHAR(36),
    user_id VARCHAR(36),
    session_id VARCHAR(36),
    provider_id VARCHAR(36),
    prompt_id VARCHAR(36),
    prompt_version INTEGER,
    input_json TEXT DEFAULT '{}',
    output_json TEXT DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'QUEUED',
    human_review_required BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_platform_audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(100),
    actor VARCHAR(255) DEFAULT 'SYSTEM',
    detail_json TEXT DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_platform_usage_metrics (
    id VARCHAR(36) PRIMARY KEY,
    provider_id VARCHAR(36),
    task_type VARCHAR(100),
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    requests INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_platform_governance_policies (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36),
    policy_code VARCHAR(50) UNIQUE NOT NULL,
    advisory_only BOOLEAN DEFAULT TRUE,
    phi_redaction_required BOOLEAN DEFAULT TRUE,
    human_review_required BOOLEAN DEFAULT TRUE,
    allowed_task_types_json TEXT DEFAULT '[]',
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_platform_memory_sessions (
    id VARCHAR(36) PRIMARY KEY,
    session_code VARCHAR(50) UNIQUE NOT NULL,
    organization_id VARCHAR(36),
    user_id VARCHAR(36),
    context_type VARCHAR(50) DEFAULT 'GENERAL',
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_platform_memory_messages (
    id VARCHAR(36) PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    role VARCHAR(30) NOT NULL,
    content_redacted TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_platform_rag_documents (
    id VARCHAR(36) PRIMARY KEY,
    organization_id VARCHAR(36),
    document_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) DEFAULT 'KNOWLEDGE',
    status VARCHAR(50) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_platform_rag_chunks (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) NOT NULL,
    chunk_index INTEGER DEFAULT 0,
    content TEXT NOT NULL,
    token_estimate INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_jobs_org ON ai_platform_inference_jobs(organization_id);
CREATE INDEX IF NOT EXISTS idx_ai_memory_org ON ai_platform_memory_sessions(organization_id);
CREATE INDEX IF NOT EXISTS idx_ai_rag_org ON ai_platform_rag_documents(organization_id);
