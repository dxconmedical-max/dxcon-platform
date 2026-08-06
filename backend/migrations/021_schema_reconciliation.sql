-- DxCon full schema reconciliation — additive, idempotent.
-- Generated from SQLAlchemy metadata. PostgreSQL only.
--
-- Rules:
--   * CREATE TABLE IF NOT EXISTS (PK skeleton)
--   * ADD COLUMN IF NOT EXISTS
--   * CREATE INDEX IF NOT EXISTS
--   * ADD CONSTRAINT only when missing (DO blocks)
--   * never DROP / ALTER TYPE / DELETE
--
-- Generated at: 2026-07-30T12:03:32.278358+00:00
-- ORM tables: 375

-- ===== ai_platform_audit_logs =====
CREATE TABLE IF NOT EXISTS ai_platform_audit_logs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ai_platform_audit_logs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ai_platform_audit_logs ADD COLUMN IF NOT EXISTS action VARCHAR(100);
ALTER TABLE ai_platform_audit_logs ADD COLUMN IF NOT EXISTS resource_type VARCHAR(100);
ALTER TABLE ai_platform_audit_logs ADD COLUMN IF NOT EXISTS resource_id VARCHAR(100);
ALTER TABLE ai_platform_audit_logs ADD COLUMN IF NOT EXISTS actor VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE ai_platform_audit_logs ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE ai_platform_audit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_ai_platform_audit_logs_action ON ai_platform_audit_logs (action);



-- ===== ai_platform_governance_policies =====
CREATE TABLE IF NOT EXISTS ai_platform_governance_policies (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ai_platform_governance_policies ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ai_platform_governance_policies ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE ai_platform_governance_policies ADD COLUMN IF NOT EXISTS policy_code VARCHAR(50);
ALTER TABLE ai_platform_governance_policies ADD COLUMN IF NOT EXISTS advisory_only BOOLEAN DEFAULT TRUE;
ALTER TABLE ai_platform_governance_policies ADD COLUMN IF NOT EXISTS phi_redaction_required BOOLEAN DEFAULT TRUE;
ALTER TABLE ai_platform_governance_policies ADD COLUMN IF NOT EXISTS human_review_required BOOLEAN DEFAULT TRUE;
ALTER TABLE ai_platform_governance_policies ADD COLUMN IF NOT EXISTS allowed_task_types_json TEXT DEFAULT '["interpretation","summary","general"]';
ALTER TABLE ai_platform_governance_policies ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE ai_platform_governance_policies ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_ai_platform_governance_policies_organization_id ON ai_platform_governance_policies (organization_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_platform_governance_policies_policy_code ON ai_platform_governance_policies (policy_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ai_platform_governance_policies_policy_code'
  ) THEN
    ALTER TABLE ai_platform_governance_policies
      ADD CONSTRAINT uq_ai_platform_governance_policies_policy_code UNIQUE (policy_code);
  END IF;
END $$;


-- ===== ai_platform_inference_jobs =====
CREATE TABLE IF NOT EXISTS ai_platform_inference_jobs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS job_code VARCHAR(50);
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS session_id VARCHAR(36);
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS prompt_id VARCHAR(36);
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS prompt_version INTEGER;
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS input_json TEXT DEFAULT '{}';
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS output_json TEXT DEFAULT '{}';
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'QUEUED';
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS human_review_required BOOLEAN DEFAULT TRUE;
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ai_platform_inference_jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_platform_inference_jobs_job_code ON ai_platform_inference_jobs (job_code);
CREATE INDEX IF NOT EXISTS ix_ai_platform_inference_jobs_organization_id ON ai_platform_inference_jobs (organization_id);
CREATE INDEX IF NOT EXISTS ix_ai_platform_inference_jobs_user_id ON ai_platform_inference_jobs (user_id);
CREATE INDEX IF NOT EXISTS ix_ai_platform_inference_jobs_session_id ON ai_platform_inference_jobs (session_id);
CREATE INDEX IF NOT EXISTS ix_ai_platform_inference_jobs_provider_id ON ai_platform_inference_jobs (provider_id);
CREATE INDEX IF NOT EXISTS ix_ai_platform_inference_jobs_prompt_id ON ai_platform_inference_jobs (prompt_id);
CREATE INDEX IF NOT EXISTS ix_ai_platform_inference_jobs_status ON ai_platform_inference_jobs (status);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ai_platform_inference_jobs_job_code'
  ) THEN
    ALTER TABLE ai_platform_inference_jobs
      ADD CONSTRAINT uq_ai_platform_inference_jobs_job_code UNIQUE (job_code);
  END IF;
END $$;


-- ===== ai_platform_memory_messages =====
CREATE TABLE IF NOT EXISTS ai_platform_memory_messages (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ai_platform_memory_messages ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ai_platform_memory_messages ADD COLUMN IF NOT EXISTS session_id VARCHAR(36);
ALTER TABLE ai_platform_memory_messages ADD COLUMN IF NOT EXISTS role VARCHAR(30);
ALTER TABLE ai_platform_memory_messages ADD COLUMN IF NOT EXISTS content_redacted TEXT;
ALTER TABLE ai_platform_memory_messages ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_ai_platform_memory_messages_session_id ON ai_platform_memory_messages (session_id);


DO $$
BEGIN
  IF to_regclass('public.ai_platform_memory_sessions') IS NULL THEN
    RAISE NOTICE 'ai_platform_memory_sessions missing — skip FK fk_ai_platform_memory_messages_session_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ai_platform_memory_messages_session_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ai_platform_memory_messages
    ADD CONSTRAINT fk_ai_platform_memory_messages_session_id
    FOREIGN KEY (session_id) REFERENCES ai_platform_memory_sessions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ai_platform_memory_messages_session_id: %', SQLERRM;
END $$;

-- ===== ai_platform_memory_sessions =====
CREATE TABLE IF NOT EXISTS ai_platform_memory_sessions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ai_platform_memory_sessions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ai_platform_memory_sessions ADD COLUMN IF NOT EXISTS session_code VARCHAR(50);
ALTER TABLE ai_platform_memory_sessions ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE ai_platform_memory_sessions ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);
ALTER TABLE ai_platform_memory_sessions ADD COLUMN IF NOT EXISTS context_type VARCHAR(50) DEFAULT 'GENERAL';
ALTER TABLE ai_platform_memory_sessions ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE ai_platform_memory_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ai_platform_memory_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_platform_memory_sessions_session_code ON ai_platform_memory_sessions (session_code);
CREATE INDEX IF NOT EXISTS ix_ai_platform_memory_sessions_organization_id ON ai_platform_memory_sessions (organization_id);
CREATE INDEX IF NOT EXISTS ix_ai_platform_memory_sessions_user_id ON ai_platform_memory_sessions (user_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ai_platform_memory_sessions_session_code'
  ) THEN
    ALTER TABLE ai_platform_memory_sessions
      ADD CONSTRAINT uq_ai_platform_memory_sessions_session_code UNIQUE (session_code);
  END IF;
END $$;


-- ===== ai_platform_prompt_versions =====
CREATE TABLE IF NOT EXISTS ai_platform_prompt_versions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ai_platform_prompt_versions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ai_platform_prompt_versions ADD COLUMN IF NOT EXISTS prompt_id VARCHAR(36);
ALTER TABLE ai_platform_prompt_versions ADD COLUMN IF NOT EXISTS version INTEGER;
ALTER TABLE ai_platform_prompt_versions ADD COLUMN IF NOT EXISTS template_text TEXT;
ALTER TABLE ai_platform_prompt_versions ADD COLUMN IF NOT EXISTS metadata_json TEXT DEFAULT '{}';
ALTER TABLE ai_platform_prompt_versions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_ai_platform_prompt_versions_prompt_id ON ai_platform_prompt_versions (prompt_id);


DO $$
BEGIN
  IF to_regclass('public.ai_platform_prompts') IS NULL THEN
    RAISE NOTICE 'ai_platform_prompts missing — skip FK fk_ai_platform_prompt_versions_prompt_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ai_platform_prompt_versions_prompt_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ai_platform_prompt_versions
    ADD CONSTRAINT fk_ai_platform_prompt_versions_prompt_id
    FOREIGN KEY (prompt_id) REFERENCES ai_platform_prompts (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ai_platform_prompt_versions_prompt_id: %', SQLERRM;
END $$;

-- ===== ai_platform_prompts =====
CREATE TABLE IF NOT EXISTS ai_platform_prompts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ai_platform_prompts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ai_platform_prompts ADD COLUMN IF NOT EXISTS prompt_code VARCHAR(100);
ALTER TABLE ai_platform_prompts ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE ai_platform_prompts ADD COLUMN IF NOT EXISTS task_type VARCHAR(100);
ALTER TABLE ai_platform_prompts ADD COLUMN IF NOT EXISTS active_version INTEGER DEFAULT 1;
ALTER TABLE ai_platform_prompts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_platform_prompts_prompt_code ON ai_platform_prompts (prompt_code);
CREATE INDEX IF NOT EXISTS ix_ai_platform_prompts_task_type ON ai_platform_prompts (task_type);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ai_platform_prompts_prompt_code'
  ) THEN
    ALTER TABLE ai_platform_prompts
      ADD CONSTRAINT uq_ai_platform_prompts_prompt_code UNIQUE (prompt_code);
  END IF;
END $$;


-- ===== ai_platform_providers =====
CREATE TABLE IF NOT EXISTS ai_platform_providers (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ai_platform_providers ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ai_platform_providers ADD COLUMN IF NOT EXISTS provider_code VARCHAR(50);
ALTER TABLE ai_platform_providers ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE ai_platform_providers ADD COLUMN IF NOT EXISTS provider_type VARCHAR(50);
ALTER TABLE ai_platform_providers ADD COLUMN IF NOT EXISTS model_name VARCHAR(100) DEFAULT 'local-advisory';
ALTER TABLE ai_platform_providers ADD COLUMN IF NOT EXISTS config_json TEXT DEFAULT '{}';
ALTER TABLE ai_platform_providers ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE ai_platform_providers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_platform_providers_provider_code ON ai_platform_providers (provider_code);
CREATE INDEX IF NOT EXISTS ix_ai_platform_providers_provider_type ON ai_platform_providers (provider_type);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ai_platform_providers_provider_code'
  ) THEN
    ALTER TABLE ai_platform_providers
      ADD CONSTRAINT uq_ai_platform_providers_provider_code UNIQUE (provider_code);
  END IF;
END $$;


-- ===== ai_platform_rag_chunks =====
CREATE TABLE IF NOT EXISTS ai_platform_rag_chunks (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ai_platform_rag_chunks ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ai_platform_rag_chunks ADD COLUMN IF NOT EXISTS document_id VARCHAR(36);
ALTER TABLE ai_platform_rag_chunks ADD COLUMN IF NOT EXISTS chunk_index INTEGER DEFAULT 0;
ALTER TABLE ai_platform_rag_chunks ADD COLUMN IF NOT EXISTS content TEXT;
ALTER TABLE ai_platform_rag_chunks ADD COLUMN IF NOT EXISTS token_estimate INTEGER DEFAULT 0;
ALTER TABLE ai_platform_rag_chunks ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_ai_platform_rag_chunks_document_id ON ai_platform_rag_chunks (document_id);


DO $$
BEGIN
  IF to_regclass('public.ai_platform_rag_documents') IS NULL THEN
    RAISE NOTICE 'ai_platform_rag_documents missing — skip FK fk_ai_platform_rag_chunks_document_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ai_platform_rag_chunks_document_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ai_platform_rag_chunks
    ADD CONSTRAINT fk_ai_platform_rag_chunks_document_id
    FOREIGN KEY (document_id) REFERENCES ai_platform_rag_documents (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ai_platform_rag_chunks_document_id: %', SQLERRM;
END $$;

-- ===== ai_platform_rag_documents =====
CREATE TABLE IF NOT EXISTS ai_platform_rag_documents (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ai_platform_rag_documents ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ai_platform_rag_documents ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE ai_platform_rag_documents ADD COLUMN IF NOT EXISTS document_code VARCHAR(50);
ALTER TABLE ai_platform_rag_documents ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE ai_platform_rag_documents ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) DEFAULT 'KNOWLEDGE';
ALTER TABLE ai_platform_rag_documents ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE ai_platform_rag_documents ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_ai_platform_rag_documents_organization_id ON ai_platform_rag_documents (organization_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_ai_platform_rag_documents_document_code ON ai_platform_rag_documents (document_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ai_platform_rag_documents_document_code'
  ) THEN
    ALTER TABLE ai_platform_rag_documents
      ADD CONSTRAINT uq_ai_platform_rag_documents_document_code UNIQUE (document_code);
  END IF;
END $$;


-- ===== ai_platform_usage_metrics =====
CREATE TABLE IF NOT EXISTS ai_platform_usage_metrics (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ai_platform_usage_metrics ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ai_platform_usage_metrics ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE ai_platform_usage_metrics ADD COLUMN IF NOT EXISTS task_type VARCHAR(100);
ALTER TABLE ai_platform_usage_metrics ADD COLUMN IF NOT EXISTS tokens_in INTEGER DEFAULT 0;
ALTER TABLE ai_platform_usage_metrics ADD COLUMN IF NOT EXISTS tokens_out INTEGER DEFAULT 0;
ALTER TABLE ai_platform_usage_metrics ADD COLUMN IF NOT EXISTS requests INTEGER DEFAULT 1;
ALTER TABLE ai_platform_usage_metrics ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_ai_platform_usage_metrics_provider_id ON ai_platform_usage_metrics (provider_id);
CREATE INDEX IF NOT EXISTS ix_ai_platform_usage_metrics_task_type ON ai_platform_usage_metrics (task_type);



-- ===== alerts =====
CREATE TABLE IF NOT EXISTS alerts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE alerts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS alert_code VARCHAR(50);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS alert_type VARCHAR(100);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS severity VARCHAR(30) DEFAULT 'MEDIUM';
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS source_type VARCHAR(100);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS source_id VARCHAR(100);
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'OPEN';
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE alerts ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_alerts_alert_code ON alerts (alert_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_alerts_alert_code'
  ) THEN
    ALTER TABLE alerts
      ADD CONSTRAINT uq_alerts_alert_code UNIQUE (alert_code);
  END IF;
END $$;


-- ===== api_clients =====
CREATE TABLE IF NOT EXISTS api_clients (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE api_clients ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE api_clients ADD COLUMN IF NOT EXISTS client_code VARCHAR(50);
ALTER TABLE api_clients ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE api_clients ADD COLUMN IF NOT EXISTS organization VARCHAR(255);
ALTER TABLE api_clients ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255);
ALTER TABLE api_clients ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE api_clients ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_api_clients_client_code ON api_clients (client_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_api_clients_client_code'
  ) THEN
    ALTER TABLE api_clients
      ADD CONSTRAINT uq_api_clients_client_code UNIQUE (client_code);
  END IF;
END $$;


-- ===== api_keys =====
CREATE TABLE IF NOT EXISTS api_keys (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS client_id VARCHAR(36);
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS key_prefix VARCHAR(20);
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS key_hash VARCHAR(255);
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE api_keys ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_api_keys_key_prefix ON api_keys (key_prefix);


DO $$
BEGIN
  IF to_regclass('public.api_clients') IS NULL THEN
    RAISE NOTICE 'api_clients missing — skip FK fk_api_keys_client_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_api_keys_client_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE api_keys
    ADD CONSTRAINT fk_api_keys_client_id
    FOREIGN KEY (client_id) REFERENCES api_clients (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_api_keys_client_id: %', SQLERRM;
END $$;

-- ===== api_usage_logs =====
CREATE TABLE IF NOT EXISTS api_usage_logs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE api_usage_logs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE api_usage_logs ADD COLUMN IF NOT EXISTS client_id VARCHAR(36);
ALTER TABLE api_usage_logs ADD COLUMN IF NOT EXISTS api_key_id VARCHAR(36);
ALTER TABLE api_usage_logs ADD COLUMN IF NOT EXISTS method VARCHAR(20);
ALTER TABLE api_usage_logs ADD COLUMN IF NOT EXISTS path VARCHAR(500);
ALTER TABLE api_usage_logs ADD COLUMN IF NOT EXISTS status_code INTEGER;
ALTER TABLE api_usage_logs ADD COLUMN IF NOT EXISTS duration_ms FLOAT DEFAULT 0;
ALTER TABLE api_usage_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.api_clients') IS NULL THEN
    RAISE NOTICE 'api_clients missing — skip FK fk_api_usage_logs_client_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_api_usage_logs_client_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE api_usage_logs
    ADD CONSTRAINT fk_api_usage_logs_client_id
    FOREIGN KEY (client_id) REFERENCES api_clients (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_api_usage_logs_client_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.api_keys') IS NULL THEN
    RAISE NOTICE 'api_keys missing — skip FK fk_api_usage_logs_api_key_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_api_usage_logs_api_key_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE api_usage_logs
    ADD CONSTRAINT fk_api_usage_logs_api_key_id
    FOREIGN KEY (api_key_id) REFERENCES api_keys (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_api_usage_logs_api_key_id: %', SQLERRM;
END $$;

-- ===== audit_logs =====
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS user_email VARCHAR(255);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS action VARCHAR(255);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS object_type VARCHAR(100);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS object_id VARCHAR(100);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS ip_address VARCHAR(100);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS request_id VARCHAR(36);
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== battery_events =====
CREATE TABLE IF NOT EXISTS battery_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE battery_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE battery_events ADD COLUMN IF NOT EXISTS device_id VARCHAR(36);
ALTER TABLE battery_events ADD COLUMN IF NOT EXISTS battery_percent FLOAT;
ALTER TABLE battery_events ADD COLUMN IF NOT EXISTS recorded_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.iot_devices') IS NULL THEN
    RAISE NOTICE 'iot_devices missing — skip FK fk_battery_events_device_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_battery_events_device_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE battery_events
    ADD CONSTRAINT fk_battery_events_device_id
    FOREIGN KEY (device_id) REFERENCES iot_devices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_battery_events_device_id: %', SQLERRM;
END $$;

-- ===== billing_accounts =====
CREATE TABLE IF NOT EXISTS billing_accounts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE billing_accounts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE billing_accounts ADD COLUMN IF NOT EXISTS account_code VARCHAR(50);
ALTER TABLE billing_accounts ADD COLUMN IF NOT EXISTS owner_type VARCHAR(50);
ALTER TABLE billing_accounts ADD COLUMN IF NOT EXISTS owner_id VARCHAR(36);
ALTER TABLE billing_accounts ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'VND';
ALTER TABLE billing_accounts ADD COLUMN IF NOT EXISTS balance FLOAT DEFAULT 0;
ALTER TABLE billing_accounts ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE billing_accounts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_billing_accounts_account_code ON billing_accounts (account_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_billing_accounts_account_code'
  ) THEN
    ALTER TABLE billing_accounts
      ADD CONSTRAINT uq_billing_accounts_account_code UNIQUE (account_code);
  END IF;
END $$;


-- ===== billing_adjustments =====
CREATE TABLE IF NOT EXISTS billing_adjustments (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE billing_adjustments ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE billing_adjustments ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE billing_adjustments ADD COLUMN IF NOT EXISTS adjustment_type VARCHAR(50);
ALTER TABLE billing_adjustments ADD COLUMN IF NOT EXISTS amount FLOAT DEFAULT 0;
ALTER TABLE billing_adjustments ADD COLUMN IF NOT EXISTS reason TEXT;
ALTER TABLE billing_adjustments ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'PENDING';
ALTER TABLE billing_adjustments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.invoices') IS NULL THEN
    RAISE NOTICE 'invoices missing — skip FK fk_billing_adjustments_invoice_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_billing_adjustments_invoice_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE billing_adjustments
    ADD CONSTRAINT fk_billing_adjustments_invoice_id
    FOREIGN KEY (invoice_id) REFERENCES invoices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_billing_adjustments_invoice_id: %', SQLERRM;
END $$;

-- ===== billing_ledgers =====
CREATE TABLE IF NOT EXISTS billing_ledgers (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE billing_ledgers ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE billing_ledgers ADD COLUMN IF NOT EXISTS account_id VARCHAR(36);
ALTER TABLE billing_ledgers ADD COLUMN IF NOT EXISTS entry_type VARCHAR(20);
ALTER TABLE billing_ledgers ADD COLUMN IF NOT EXISTS amount FLOAT DEFAULT 0;
ALTER TABLE billing_ledgers ADD COLUMN IF NOT EXISTS reference_type VARCHAR(50);
ALTER TABLE billing_ledgers ADD COLUMN IF NOT EXISTS reference_id VARCHAR(36);
ALTER TABLE billing_ledgers ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE billing_ledgers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.billing_accounts') IS NULL THEN
    RAISE NOTICE 'billing_accounts missing — skip FK fk_billing_ledgers_account_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_billing_ledgers_account_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE billing_ledgers
    ADD CONSTRAINT fk_billing_ledgers_account_id
    FOREIGN KEY (account_id) REFERENCES billing_accounts (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_billing_ledgers_account_id: %', SQLERRM;
END $$;

-- ===== biomarkers =====
CREATE TABLE IF NOT EXISTS biomarkers (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biomarkers ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biomarkers ADD COLUMN IF NOT EXISTS biomarker_code VARCHAR(50);
ALTER TABLE biomarkers ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE biomarkers ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE biomarkers ADD COLUMN IF NOT EXISTS unit VARCHAR(50);
ALTER TABLE biomarkers ADD COLUMN IF NOT EXISTS related_biomarkers_json TEXT DEFAULT '[]';
ALTER TABLE biomarkers ADD COLUMN IF NOT EXISTS related_diseases_json TEXT DEFAULT '[]';
ALTER TABLE biomarkers ADD COLUMN IF NOT EXISTS evidence_level VARCHAR(10) DEFAULT 'B';
ALTER TABLE biomarkers ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE biomarkers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_biomarkers_biomarker_code ON biomarkers (biomarker_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biomarkers_biomarker_code'
  ) THEN
    ALTER TABLE biomarkers
      ADD CONSTRAINT uq_biomarkers_biomarker_code UNIQUE (biomarker_code);
  END IF;
END $$;


-- ===== biz_collections =====
CREATE TABLE IF NOT EXISTS biz_collections (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS collector_name VARCHAR(255);
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS pickup_address TEXT;
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'assigned';
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS sample_code VARCHAR(50);
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS barcode_value VARCHAR(100);
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS accession_number VARCHAR(50);
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS received_by VARCHAR(255);
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS received_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS condition_status VARCHAR(30);
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS receive_note TEXT;
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_collections ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_collections_sample_code ON biz_collections (sample_code);
CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_collections_barcode_value ON biz_collections (barcode_value);
CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_collections_accession_number ON biz_collections (accession_number);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_collections_barcode_value'
  ) THEN
    ALTER TABLE biz_collections
      ADD CONSTRAINT uq_biz_collections_barcode_value UNIQUE (barcode_value);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_collections_sample_code'
  ) THEN
    ALTER TABLE biz_collections
      ADD CONSTRAINT uq_biz_collections_sample_code UNIQUE (sample_code);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_collections_accession_number'
  ) THEN
    ALTER TABLE biz_collections
      ADD CONSTRAINT uq_biz_collections_accession_number UNIQUE (accession_number);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.biz_orders') IS NULL THEN
    RAISE NOTICE 'biz_orders missing — skip FK fk_biz_collections_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_collections_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_collections
    ADD CONSTRAINT fk_biz_collections_order_id
    FOREIGN KEY (order_id) REFERENCES biz_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_collections_order_id: %', SQLERRM;
END $$;

-- ===== biz_invoices =====
CREATE TABLE IF NOT EXISTS biz_invoices (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biz_invoices ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biz_invoices ADD COLUMN IF NOT EXISTS invoice_no VARCHAR(50);
ALTER TABLE biz_invoices ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE biz_invoices ADD COLUMN IF NOT EXISTS amount FLOAT DEFAULT 0;
ALTER TABLE biz_invoices ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'unpaid';
ALTER TABLE biz_invoices ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_invoices_invoice_no ON biz_invoices (invoice_no);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_invoices_invoice_no'
  ) THEN
    ALTER TABLE biz_invoices
      ADD CONSTRAINT uq_biz_invoices_invoice_no UNIQUE (invoice_no);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.biz_orders') IS NULL THEN
    RAISE NOTICE 'biz_orders missing — skip FK fk_biz_invoices_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_invoices_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_invoices
    ADD CONSTRAINT fk_biz_invoices_order_id
    FOREIGN KEY (order_id) REFERENCES biz_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_invoices_order_id: %', SQLERRM;
END $$;

-- ===== biz_lab_queue_items =====
CREATE TABLE IF NOT EXISTS biz_lab_queue_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS order_code VARCHAR(50);
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS stage VARCHAR(30) DEFAULT 'waiting';
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'routine';
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS queue_reference VARCHAR(100);
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS laboratory_name VARCHAR(255);
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS entered_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS verified_by VARCHAR(255);
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255);
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_lab_queue_items ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_lab_queue_items_order_id ON biz_lab_queue_items (order_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_lab_queue_items_order_code ON biz_lab_queue_items (order_code);
CREATE INDEX IF NOT EXISTS ix_biz_lab_queue_items_stage ON biz_lab_queue_items (stage);
CREATE INDEX IF NOT EXISTS ix_biz_lab_queue_items_priority ON biz_lab_queue_items (priority);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_lab_queue_items_order_id'
  ) THEN
    ALTER TABLE biz_lab_queue_items
      ADD CONSTRAINT uq_biz_lab_queue_items_order_id UNIQUE (order_id);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.biz_orders') IS NULL THEN
    RAISE NOTICE 'biz_orders missing — skip FK fk_biz_lab_queue_items_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_lab_queue_items_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_lab_queue_items
    ADD CONSTRAINT fk_biz_lab_queue_items_order_id
    FOREIGN KEY (order_id) REFERENCES biz_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_lab_queue_items_order_id: %', SQLERRM;
END $$;

-- ===== biz_order_items =====
CREATE TABLE IF NOT EXISTS biz_order_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biz_order_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biz_order_items ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE biz_order_items ADD COLUMN IF NOT EXISTS test_catalog_id VARCHAR(36);
ALTER TABLE biz_order_items ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE biz_order_items ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE biz_order_items ADD COLUMN IF NOT EXISTS unit_price FLOAT DEFAULT 0;
ALTER TABLE biz_order_items ADD COLUMN IF NOT EXISTS quantity INTEGER DEFAULT 1;
ALTER TABLE biz_order_items ADD COLUMN IF NOT EXISTS line_total FLOAT DEFAULT 0;
ALTER TABLE biz_order_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.biz_orders') IS NULL THEN
    RAISE NOTICE 'biz_orders missing — skip FK fk_biz_order_items_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_order_items_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_order_items
    ADD CONSTRAINT fk_biz_order_items_order_id
    FOREIGN KEY (order_id) REFERENCES biz_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_order_items_order_id: %', SQLERRM;
END $$;

-- ===== biz_orders =====
CREATE TABLE IF NOT EXISTS biz_orders (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS order_code VARCHAR(50);
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS patient_code VARCHAR(50);
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS patient_name VARCHAR(255);
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'draft';
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS subtotal FLOAT DEFAULT 0;
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS discount FLOAT DEFAULT 0;
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS total_amount FLOAT DEFAULT 0;
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS barcode_value VARCHAR(100);
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_orders_order_code ON biz_orders (order_code);
CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_orders_barcode_value ON biz_orders (barcode_value);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_orders_order_code'
  ) THEN
    ALTER TABLE biz_orders
      ADD CONSTRAINT uq_biz_orders_order_code UNIQUE (order_code);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_orders_barcode_value'
  ) THEN
    ALTER TABLE biz_orders
      ADD CONSTRAINT uq_biz_orders_barcode_value UNIQUE (barcode_value);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_biz_orders_patient_code';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_orders_patient_code'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_orders
    ADD CONSTRAINT fk_biz_orders_patient_code
    FOREIGN KEY (patient_code) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_orders_patient_code: %', SQLERRM;
END $$;

-- ===== biz_payments =====
CREATE TABLE IF NOT EXISTS biz_payments (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biz_payments ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biz_payments ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE biz_payments ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE biz_payments ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50);
ALTER TABLE biz_payments ADD COLUMN IF NOT EXISTS receipt_number VARCHAR(50);
ALTER TABLE biz_payments ADD COLUMN IF NOT EXISTS amount FLOAT DEFAULT 0;
ALTER TABLE biz_payments ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_payments ADD COLUMN IF NOT EXISTS created_by VARCHAR(255);
ALTER TABLE biz_payments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_payments_receipt_number ON biz_payments (receipt_number);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_payments_receipt_number'
  ) THEN
    ALTER TABLE biz_payments
      ADD CONSTRAINT uq_biz_payments_receipt_number UNIQUE (receipt_number);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.biz_invoices') IS NULL THEN
    RAISE NOTICE 'biz_invoices missing — skip FK fk_biz_payments_invoice_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_payments_invoice_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_payments
    ADD CONSTRAINT fk_biz_payments_invoice_id
    FOREIGN KEY (invoice_id) REFERENCES biz_invoices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_payments_invoice_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.biz_orders') IS NULL THEN
    RAISE NOTICE 'biz_orders missing — skip FK fk_biz_payments_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_payments_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_payments
    ADD CONSTRAINT fk_biz_payments_order_id
    FOREIGN KEY (order_id) REFERENCES biz_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_payments_order_id: %', SQLERRM;
END $$;

-- ===== biz_receipts =====
CREATE TABLE IF NOT EXISTS biz_receipts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS receipt_code VARCHAR(50);
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS payment_id VARCHAR(36);
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'issued';
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS print_count INTEGER DEFAULT 0;
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS preferred_format VARCHAR(30) DEFAULT 'standard';
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS html_snapshot TEXT;
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS thermal_payload TEXT;
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS pdf_path VARCHAR(500);
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS issued_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS issued_by VARCHAR(255);
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS last_printed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS last_printed_by VARCHAR(255);
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS cancelled_by VARCHAR(255);
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS cancel_reason TEXT;
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_receipts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_receipts_receipt_code ON biz_receipts (receipt_code);
CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_receipts_payment_id ON biz_receipts (payment_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_receipts_payment_id'
  ) THEN
    ALTER TABLE biz_receipts
      ADD CONSTRAINT uq_biz_receipts_payment_id UNIQUE (payment_id);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_receipts_receipt_code'
  ) THEN
    ALTER TABLE biz_receipts
      ADD CONSTRAINT uq_biz_receipts_receipt_code UNIQUE (receipt_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.biz_payments') IS NULL THEN
    RAISE NOTICE 'biz_payments missing — skip FK fk_biz_receipts_payment_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_receipts_payment_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_receipts
    ADD CONSTRAINT fk_biz_receipts_payment_id
    FOREIGN KEY (payment_id) REFERENCES biz_payments (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_receipts_payment_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.biz_orders') IS NULL THEN
    RAISE NOTICE 'biz_orders missing — skip FK fk_biz_receipts_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_receipts_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_receipts
    ADD CONSTRAINT fk_biz_receipts_order_id
    FOREIGN KEY (order_id) REFERENCES biz_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_receipts_order_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.biz_invoices') IS NULL THEN
    RAISE NOTICE 'biz_invoices missing — skip FK fk_biz_receipts_invoice_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_receipts_invoice_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_receipts
    ADD CONSTRAINT fk_biz_receipts_invoice_id
    FOREIGN KEY (invoice_id) REFERENCES biz_invoices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_receipts_invoice_id: %', SQLERRM;
END $$;

-- ===== biz_result_items =====
CREATE TABLE IF NOT EXISTS biz_result_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS result_id VARCHAR(36);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS result_value VARCHAR(255);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS unit VARCHAR(50);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS reference_range VARCHAR(255);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS flag VARCHAR(20) DEFAULT 'NORMAL';
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS instrument VARCHAR(100);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS technician VARCHAR(255);
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS result_time TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS entry_note TEXT;
ALTER TABLE biz_result_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.biz_results') IS NULL THEN
    RAISE NOTICE 'biz_results missing — skip FK fk_biz_result_items_result_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_result_items_result_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_result_items
    ADD CONSTRAINT fk_biz_result_items_result_id
    FOREIGN KEY (result_id) REFERENCES biz_results (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_result_items_result_id: %', SQLERRM;
END $$;

-- ===== biz_results =====
CREATE TABLE IF NOT EXISTS biz_results (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS result_code VARCHAR(50);
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'testing';
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS doctor_note TEXT;
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS approved_by VARCHAR(255);
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS released_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS html_content TEXT;
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS patient_visible BOOLEAN DEFAULT FALSE;
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS workflow_status VARCHAR(30) DEFAULT 'draft';
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS result_source VARCHAR(30) DEFAULT 'manual';
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS import_batch_id VARCHAR(36);
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_results ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_results_result_code ON biz_results (result_code);
CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_results_order_id ON biz_results (order_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_results_order_id'
  ) THEN
    ALTER TABLE biz_results
      ADD CONSTRAINT uq_biz_results_order_id UNIQUE (order_id);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_results_result_code'
  ) THEN
    ALTER TABLE biz_results
      ADD CONSTRAINT uq_biz_results_result_code UNIQUE (result_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.biz_orders') IS NULL THEN
    RAISE NOTICE 'biz_orders missing — skip FK fk_biz_results_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_results_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_results
    ADD CONSTRAINT fk_biz_results_order_id
    FOREIGN KEY (order_id) REFERENCES biz_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_results_order_id: %', SQLERRM;
END $$;

-- ===== biz_sample_queue_events =====
CREATE TABLE IF NOT EXISTS biz_sample_queue_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biz_sample_queue_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biz_sample_queue_events ADD COLUMN IF NOT EXISTS queue_item_id VARCHAR(36);
ALTER TABLE biz_sample_queue_events ADD COLUMN IF NOT EXISTS order_code VARCHAR(50);
ALTER TABLE biz_sample_queue_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(50);
ALTER TABLE biz_sample_queue_events ADD COLUMN IF NOT EXISTS from_stage VARCHAR(30);
ALTER TABLE biz_sample_queue_events ADD COLUMN IF NOT EXISTS to_stage VARCHAR(30);
ALTER TABLE biz_sample_queue_events ADD COLUMN IF NOT EXISTS actor VARCHAR(255);
ALTER TABLE biz_sample_queue_events ADD COLUMN IF NOT EXISTS location VARCHAR(255);
ALTER TABLE biz_sample_queue_events ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE biz_sample_queue_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_biz_sample_queue_events_queue_item_id ON biz_sample_queue_events (queue_item_id);
CREATE INDEX IF NOT EXISTS ix_biz_sample_queue_events_order_code ON biz_sample_queue_events (order_code);
CREATE INDEX IF NOT EXISTS ix_biz_sample_queue_events_created_at ON biz_sample_queue_events (created_at);


DO $$
BEGIN
  IF to_regclass('public.biz_sample_queue_items') IS NULL THEN
    RAISE NOTICE 'biz_sample_queue_items missing — skip FK fk_biz_sample_queue_events_queue_item_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_sample_queue_events_queue_item_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_sample_queue_events
    ADD CONSTRAINT fk_biz_sample_queue_events_queue_item_id
    FOREIGN KEY (queue_item_id) REFERENCES biz_sample_queue_items (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_sample_queue_events_queue_item_id: %', SQLERRM;
END $$;

-- ===== biz_sample_queue_items =====
CREATE TABLE IF NOT EXISTS biz_sample_queue_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS order_code VARCHAR(50);
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS collection_id VARCHAR(36);
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS sample_code VARCHAR(50);
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS stage VARCHAR(30) DEFAULT 'collected';
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS collector_name VARCHAR(255);
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS location VARCHAR(255);
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS collected_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS transport_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS received_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS sorting_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS laboratory_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255);
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE biz_sample_queue_items ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_sample_queue_items_order_id ON biz_sample_queue_items (order_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_biz_sample_queue_items_order_code ON biz_sample_queue_items (order_code);
CREATE INDEX IF NOT EXISTS ix_biz_sample_queue_items_sample_code ON biz_sample_queue_items (sample_code);
CREATE INDEX IF NOT EXISTS ix_biz_sample_queue_items_stage ON biz_sample_queue_items (stage);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_biz_sample_queue_items_order_id'
  ) THEN
    ALTER TABLE biz_sample_queue_items
      ADD CONSTRAINT uq_biz_sample_queue_items_order_id UNIQUE (order_id);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.biz_collections') IS NULL THEN
    RAISE NOTICE 'biz_collections missing — skip FK fk_biz_sample_queue_items_collection_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_sample_queue_items_collection_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_sample_queue_items
    ADD CONSTRAINT fk_biz_sample_queue_items_collection_id
    FOREIGN KEY (collection_id) REFERENCES biz_collections (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_sample_queue_items_collection_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.biz_orders') IS NULL THEN
    RAISE NOTICE 'biz_orders missing — skip FK fk_biz_sample_queue_items_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_biz_sample_queue_items_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE biz_sample_queue_items
    ADD CONSTRAINT fk_biz_sample_queue_items_order_id
    FOREIGN KEY (order_id) REFERENCES biz_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_biz_sample_queue_items_order_id: %', SQLERRM;
END $$;

-- ===== biz_workflow_audits =====
CREATE TABLE IF NOT EXISTS biz_workflow_audits (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE biz_workflow_audits ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE biz_workflow_audits ADD COLUMN IF NOT EXISTS actor VARCHAR(255);
ALTER TABLE biz_workflow_audits ADD COLUMN IF NOT EXISTS action VARCHAR(100);
ALTER TABLE biz_workflow_audits ADD COLUMN IF NOT EXISTS entity_type VARCHAR(50);
ALTER TABLE biz_workflow_audits ADD COLUMN IF NOT EXISTS entity_id VARCHAR(100);
ALTER TABLE biz_workflow_audits ADD COLUMN IF NOT EXISTS old_status VARCHAR(50);
ALTER TABLE biz_workflow_audits ADD COLUMN IF NOT EXISTS new_status VARCHAR(50);
ALTER TABLE biz_workflow_audits ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE biz_workflow_audits ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== booking_assignments =====
CREATE TABLE IF NOT EXISTS booking_assignments (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE booking_assignments ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE booking_assignments ADD COLUMN IF NOT EXISTS booking_id VARCHAR(36);
ALTER TABLE booking_assignments ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE booking_assignments ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE booking_assignments ADD COLUMN IF NOT EXISTS scheduled_slot_id VARCHAR(36);
ALTER TABLE booking_assignments ADD COLUMN IF NOT EXISTS assignment_status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE booking_assignments ADD COLUMN IF NOT EXISTS assigned_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE booking_assignments ADD COLUMN IF NOT EXISTS accepted_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE booking_assignments ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE booking_assignments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE booking_assignments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_booking_assignments_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_booking_assignments_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE booking_assignments
    ADD CONSTRAINT fk_booking_assignments_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_booking_assignments_partner_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.marketplace_bookings') IS NULL THEN
    RAISE NOTICE 'marketplace_bookings missing — skip FK fk_booking_assignments_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_booking_assignments_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE booking_assignments
    ADD CONSTRAINT fk_booking_assignments_booking_id
    FOREIGN KEY (booking_id) REFERENCES marketplace_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_booking_assignments_booking_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.scheduling_slots') IS NULL THEN
    RAISE NOTICE 'scheduling_slots missing — skip FK fk_booking_assignments_scheduled_slot_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_booking_assignments_scheduled_slot_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE booking_assignments
    ADD CONSTRAINT fk_booking_assignments_scheduled_slot_id
    FOREIGN KEY (scheduled_slot_id) REFERENCES scheduling_slots (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_booking_assignments_scheduled_slot_id: %', SQLERRM;
END $$;

-- ===== clinic_analytics =====
CREATE TABLE IF NOT EXISTS clinic_analytics (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinic_analytics ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinic_analytics ADD COLUMN IF NOT EXISTS analytics_code VARCHAR(50);
ALTER TABLE clinic_analytics ADD COLUMN IF NOT EXISTS period_start TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE clinic_analytics ADD COLUMN IF NOT EXISTS period_end TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE clinic_analytics ADD COLUMN IF NOT EXISTS clinic_id VARCHAR(36);
ALTER TABLE clinic_analytics ADD COLUMN IF NOT EXISTS orders_total INTEGER DEFAULT 0;
ALTER TABLE clinic_analytics ADD COLUMN IF NOT EXISTS revenue_total FLOAT DEFAULT 0;
ALTER TABLE clinic_analytics ADD COLUMN IF NOT EXISTS patient_count INTEGER DEFAULT 0;
ALTER TABLE clinic_analytics ADD COLUMN IF NOT EXISTS metrics_json TEXT DEFAULT '{}';
ALTER TABLE clinic_analytics ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clinic_analytics_analytics_code ON clinic_analytics (analytics_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinic_analytics_analytics_code'
  ) THEN
    ALTER TABLE clinic_analytics
      ADD CONSTRAINT uq_clinic_analytics_analytics_code UNIQUE (analytics_code);
  END IF;
END $$;


-- ===== clinic_bookings =====
CREATE TABLE IF NOT EXISTS clinic_bookings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinic_bookings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinic_bookings ADD COLUMN IF NOT EXISTS booking_code VARCHAR(50);
ALTER TABLE clinic_bookings ADD COLUMN IF NOT EXISTS clinic_id VARCHAR(36);
ALTER TABLE clinic_bookings ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE clinic_bookings ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE clinic_bookings ADD COLUMN IF NOT EXISTS service_name VARCHAR(255);
ALTER TABLE clinic_bookings ADD COLUMN IF NOT EXISTS scheduled_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE clinic_bookings ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE clinic_bookings ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE clinic_bookings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clinic_bookings_booking_code ON clinic_bookings (booking_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinic_bookings_booking_code'
  ) THEN
    ALTER TABLE clinic_bookings
      ADD CONSTRAINT uq_clinic_bookings_booking_code UNIQUE (booking_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_clinic_bookings_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_clinic_bookings_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE clinic_bookings
    ADD CONSTRAINT fk_clinic_bookings_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_clinic_bookings_patient_id: %', SQLERRM;
END $$;

-- ===== clinic_departments =====
CREATE TABLE IF NOT EXISTS clinic_departments (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinic_departments ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinic_departments ADD COLUMN IF NOT EXISTS clinic_id VARCHAR(36);
ALTER TABLE clinic_departments ADD COLUMN IF NOT EXISTS department_code VARCHAR(50);
ALTER TABLE clinic_departments ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE clinic_departments ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE clinic_departments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== clinic_doctors =====
CREATE TABLE IF NOT EXISTS clinic_doctors (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinic_doctors ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinic_doctors ADD COLUMN IF NOT EXISTS clinic_id VARCHAR(36);
ALTER TABLE clinic_doctors ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE clinic_doctors ADD COLUMN IF NOT EXISTS department_id VARCHAR(36);
ALTER TABLE clinic_doctors ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'STAFF';
ALTER TABLE clinic_doctors ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE clinic_doctors ADD COLUMN IF NOT EXISTS joined_at TIMESTAMP WITHOUT TIME ZONE;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinic_doctor'
  ) THEN
    ALTER TABLE clinic_doctors
      ADD CONSTRAINT uq_clinic_doctor UNIQUE (clinic_id, doctor_id);
  END IF;
END $$;


-- ===== clinic_orders =====
CREATE TABLE IF NOT EXISTS clinic_orders (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinic_orders ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinic_orders ADD COLUMN IF NOT EXISTS order_code VARCHAR(50);
ALTER TABLE clinic_orders ADD COLUMN IF NOT EXISTS clinic_id VARCHAR(36);
ALTER TABLE clinic_orders ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE clinic_orders ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE clinic_orders ADD COLUMN IF NOT EXISTS total_amount FLOAT DEFAULT 0;
ALTER TABLE clinic_orders ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE clinic_orders ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE clinic_orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clinic_orders_order_code ON clinic_orders (order_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinic_orders_order_code'
  ) THEN
    ALTER TABLE clinic_orders
      ADD CONSTRAINT uq_clinic_orders_order_code UNIQUE (order_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_clinic_orders_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_clinic_orders_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE clinic_orders
    ADD CONSTRAINT fk_clinic_orders_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_clinic_orders_patient_id: %', SQLERRM;
END $$;

-- ===== clinic_patients =====
CREATE TABLE IF NOT EXISTS clinic_patients (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinic_patients ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinic_patients ADD COLUMN IF NOT EXISTS clinic_id VARCHAR(36);
ALTER TABLE clinic_patients ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE clinic_patients ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE clinic_patients ADD COLUMN IF NOT EXISTS registered_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE clinic_patients ADD COLUMN IF NOT EXISTS note TEXT;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinic_patient'
  ) THEN
    ALTER TABLE clinic_patients
      ADD CONSTRAINT uq_clinic_patient UNIQUE (clinic_id, patient_id);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_clinic_patients_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_clinic_patients_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE clinic_patients
    ADD CONSTRAINT fk_clinic_patients_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_clinic_patients_patient_id: %', SQLERRM;
END $$;

-- ===== clinic_profiles =====
CREATE TABLE IF NOT EXISTS clinic_profiles (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS clinic_id VARCHAR(36);
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS clinic_code VARCHAR(50);
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS legal_name VARCHAR(255);
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS tax_code VARCHAR(50);
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS settings_json TEXT DEFAULT '{}';
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE clinic_profiles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clinic_profiles_clinic_id ON clinic_profiles (clinic_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_clinic_profiles_clinic_code ON clinic_profiles (clinic_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinic_profiles_clinic_code'
  ) THEN
    ALTER TABLE clinic_profiles
      ADD CONSTRAINT uq_clinic_profiles_clinic_code UNIQUE (clinic_code);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinic_profiles_clinic_id'
  ) THEN
    ALTER TABLE clinic_profiles
      ADD CONSTRAINT uq_clinic_profiles_clinic_id UNIQUE (clinic_id);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.enterprise_organizations') IS NULL THEN
    RAISE NOTICE 'enterprise_organizations missing — skip FK fk_clinic_profiles_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_clinic_profiles_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE clinic_profiles
    ADD CONSTRAINT fk_clinic_profiles_organization_id
    FOREIGN KEY (organization_id) REFERENCES enterprise_organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_clinic_profiles_organization_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.enterprise_tenants') IS NULL THEN
    RAISE NOTICE 'enterprise_tenants missing — skip FK fk_clinic_profiles_tenant_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_clinic_profiles_tenant_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE clinic_profiles
    ADD CONSTRAINT fk_clinic_profiles_tenant_id
    FOREIGN KEY (tenant_id) REFERENCES enterprise_tenants (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_clinic_profiles_tenant_id: %', SQLERRM;
END $$;

-- ===== clinic_referrals =====
CREATE TABLE IF NOT EXISTS clinic_referrals (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinic_referrals ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinic_referrals ADD COLUMN IF NOT EXISTS referral_code VARCHAR(50);
ALTER TABLE clinic_referrals ADD COLUMN IF NOT EXISTS clinic_id VARCHAR(36);
ALTER TABLE clinic_referrals ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE clinic_referrals ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE clinic_referrals ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE clinic_referrals ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE clinic_referrals ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE clinic_referrals ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE clinic_referrals ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clinic_referrals_referral_code ON clinic_referrals (referral_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinic_referrals_referral_code'
  ) THEN
    ALTER TABLE clinic_referrals
      ADD CONSTRAINT uq_clinic_referrals_referral_code UNIQUE (referral_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_clinic_referrals_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_clinic_referrals_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE clinic_referrals
    ADD CONSTRAINT fk_clinic_referrals_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_clinic_referrals_patient_id: %', SQLERRM;
END $$;

-- ===== clinic_revenue_summaries =====
CREATE TABLE IF NOT EXISTS clinic_revenue_summaries (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinic_revenue_summaries ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinic_revenue_summaries ADD COLUMN IF NOT EXISTS clinic_id VARCHAR(36);
ALTER TABLE clinic_revenue_summaries ADD COLUMN IF NOT EXISTS period_start TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE clinic_revenue_summaries ADD COLUMN IF NOT EXISTS period_end TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE clinic_revenue_summaries ADD COLUMN IF NOT EXISTS gross_amount FLOAT DEFAULT 0;
ALTER TABLE clinic_revenue_summaries ADD COLUMN IF NOT EXISTS net_amount FLOAT DEFAULT 0;
ALTER TABLE clinic_revenue_summaries ADD COLUMN IF NOT EXISTS orders_count INTEGER DEFAULT 0;
ALTER TABLE clinic_revenue_summaries ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_clinic_revenue_summaries_clinic_id ON clinic_revenue_summaries (clinic_id);



-- ===== clinical_delta_checks =====
CREATE TABLE IF NOT EXISTS clinical_delta_checks (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinical_delta_checks ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinical_delta_checks ADD COLUMN IF NOT EXISTS check_code VARCHAR(50);
ALTER TABLE clinical_delta_checks ADD COLUMN IF NOT EXISTS patient_id VARCHAR(36);
ALTER TABLE clinical_delta_checks ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE clinical_delta_checks ADD COLUMN IF NOT EXISTS current_value FLOAT;
ALTER TABLE clinical_delta_checks ADD COLUMN IF NOT EXISTS previous_value FLOAT;
ALTER TABLE clinical_delta_checks ADD COLUMN IF NOT EXISTS delta_percent FLOAT;
ALTER TABLE clinical_delta_checks ADD COLUMN IF NOT EXISTS is_significant BOOLEAN DEFAULT FALSE;
ALTER TABLE clinical_delta_checks ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE clinical_delta_checks ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clinical_delta_checks_check_code ON clinical_delta_checks (check_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinical_delta_checks_check_code'
  ) THEN
    ALTER TABLE clinical_delta_checks
      ADD CONSTRAINT uq_clinical_delta_checks_check_code UNIQUE (check_code);
  END IF;
END $$;


-- ===== clinical_guideline_packs =====
CREATE TABLE IF NOT EXISTS clinical_guideline_packs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinical_guideline_packs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinical_guideline_packs ADD COLUMN IF NOT EXISTS pack_code VARCHAR(50);
ALTER TABLE clinical_guideline_packs ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE clinical_guideline_packs ADD COLUMN IF NOT EXISTS panel_type VARCHAR(50);
ALTER TABLE clinical_guideline_packs ADD COLUMN IF NOT EXISTS version VARCHAR(20) DEFAULT '1.0';
ALTER TABLE clinical_guideline_packs ADD COLUMN IF NOT EXISTS rules_json TEXT DEFAULT '[]';
ALTER TABLE clinical_guideline_packs ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE clinical_guideline_packs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clinical_guideline_packs_pack_code ON clinical_guideline_packs (pack_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinical_guideline_packs_pack_code'
  ) THEN
    ALTER TABLE clinical_guideline_packs
      ADD CONSTRAINT uq_clinical_guideline_packs_pack_code UNIQUE (pack_code);
  END IF;
END $$;


-- ===== clinical_guidelines =====
CREATE TABLE IF NOT EXISTS clinical_guidelines (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinical_guidelines ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinical_guidelines ADD COLUMN IF NOT EXISTS guideline_code VARCHAR(50);
ALTER TABLE clinical_guidelines ADD COLUMN IF NOT EXISTS pack_source VARCHAR(50);
ALTER TABLE clinical_guidelines ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE clinical_guidelines ADD COLUMN IF NOT EXISTS version VARCHAR(20) DEFAULT '1.0';
ALTER TABLE clinical_guidelines ADD COLUMN IF NOT EXISTS content TEXT;
ALTER TABLE clinical_guidelines ADD COLUMN IF NOT EXISTS evidence_level VARCHAR(10) DEFAULT 'B';
ALTER TABLE clinical_guidelines ADD COLUMN IF NOT EXISTS citation_json TEXT DEFAULT '{}';
ALTER TABLE clinical_guidelines ADD COLUMN IF NOT EXISTS test_codes_json TEXT DEFAULT '[]';
ALTER TABLE clinical_guidelines ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE clinical_guidelines ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clinical_guidelines_guideline_code ON clinical_guidelines (guideline_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinical_guidelines_guideline_code'
  ) THEN
    ALTER TABLE clinical_guidelines
      ADD CONSTRAINT uq_clinical_guidelines_guideline_code UNIQUE (guideline_code);
  END IF;
END $$;


-- ===== clinical_recommendations =====
CREATE TABLE IF NOT EXISTS clinical_recommendations (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinical_recommendations ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinical_recommendations ADD COLUMN IF NOT EXISTS recommendation_code VARCHAR(50);
ALTER TABLE clinical_recommendations ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE clinical_recommendations ADD COLUMN IF NOT EXISTS recommendation_type VARCHAR(50);
ALTER TABLE clinical_recommendations ADD COLUMN IF NOT EXISTS content TEXT;
ALTER TABLE clinical_recommendations ADD COLUMN IF NOT EXISTS specialty VARCHAR(100);
ALTER TABLE clinical_recommendations ADD COLUMN IF NOT EXISTS repeat_interval_days INTEGER;
ALTER TABLE clinical_recommendations ADD COLUMN IF NOT EXISTS advisory_only BOOLEAN DEFAULT TRUE;
ALTER TABLE clinical_recommendations ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clinical_recommendations_recommendation_code ON clinical_recommendations (recommendation_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinical_recommendations_recommendation_code'
  ) THEN
    ALTER TABLE clinical_recommendations
      ADD CONSTRAINT uq_clinical_recommendations_recommendation_code UNIQUE (recommendation_code);
  END IF;
END $$;


-- ===== clinical_reports =====
CREATE TABLE IF NOT EXISTS clinical_reports (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS report_code VARCHAR(50);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS order_code VARCHAR(50);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS accession_id VARCHAR(36);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS accession_number VARCHAR(50);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS laboratory_id VARCHAR(36);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS result_id VARCHAR(36);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS report_status VARCHAR(30) DEFAULT 'draft';
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS report_version INTEGER DEFAULT 1;
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS report_type VARCHAR(30) DEFAULT 'diagnostic';
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS generated_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS approved_by VARCHAR(255);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS released_by VARCHAR(255);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS released_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS doctor_note TEXT;
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS lab_note TEXT;
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS clinical_summary TEXT;
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS pdf_path VARCHAR(500);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS report_hash VARCHAR(128);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS qr_payload VARCHAR(255);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS html_content TEXT;
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS is_visible_to_patient BOOLEAN DEFAULT FALSE;
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS amended_from_report_id VARCHAR(36);
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS amendment_reason TEXT;
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE clinical_reports ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clinical_reports_report_code ON clinical_reports (report_code);
CREATE INDEX IF NOT EXISTS ix_clinical_reports_order_id ON clinical_reports (order_id);
CREATE INDEX IF NOT EXISTS ix_clinical_reports_order_code ON clinical_reports (order_code);
CREATE INDEX IF NOT EXISTS ix_clinical_reports_patient_id ON clinical_reports (patient_id);
CREATE INDEX IF NOT EXISTS ix_clinical_reports_report_status ON clinical_reports (report_status);



-- ===== clinical_risk_assessments =====
CREATE TABLE IF NOT EXISTS clinical_risk_assessments (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinical_risk_assessments ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinical_risk_assessments ADD COLUMN IF NOT EXISTS assessment_code VARCHAR(50);
ALTER TABLE clinical_risk_assessments ADD COLUMN IF NOT EXISTS patient_id VARCHAR(36);
ALTER TABLE clinical_risk_assessments ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE clinical_risk_assessments ADD COLUMN IF NOT EXISTS risk_domain VARCHAR(50);
ALTER TABLE clinical_risk_assessments ADD COLUMN IF NOT EXISTS risk_score FLOAT DEFAULT 0;
ALTER TABLE clinical_risk_assessments ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) DEFAULT 'LOW';
ALTER TABLE clinical_risk_assessments ADD COLUMN IF NOT EXISTS algorithm VARCHAR(50);
ALTER TABLE clinical_risk_assessments ADD COLUMN IF NOT EXISTS factors_json TEXT DEFAULT '[]';
ALTER TABLE clinical_risk_assessments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clinical_risk_assessments_assessment_code ON clinical_risk_assessments (assessment_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinical_risk_assessments_assessment_code'
  ) THEN
    ALTER TABLE clinical_risk_assessments
      ADD CONSTRAINT uq_clinical_risk_assessments_assessment_code UNIQUE (assessment_code);
  END IF;
END $$;


-- ===== clinical_rule_definitions =====
CREATE TABLE IF NOT EXISTS clinical_rule_definitions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS rule_code VARCHAR(50);
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS pack_id VARCHAR(36);
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS panel_type VARCHAR(50);
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS condition_type VARCHAR(50) DEFAULT 'THRESHOLD';
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS sex VARCHAR(10) DEFAULT 'ALL';
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS age_min INTEGER DEFAULT 0;
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS age_max INTEGER DEFAULT 120;
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS threshold_low FLOAT;
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS threshold_high FLOAT;
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS delta_percent FLOAT;
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS finding_en TEXT;
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS significance_en TEXT;
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS confidence FLOAT DEFAULT 0.8;
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 100;
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE clinical_rule_definitions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_clinical_rule_definitions_rule_code ON clinical_rule_definitions (rule_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_clinical_rule_definitions_rule_code'
  ) THEN
    ALTER TABLE clinical_rule_definitions
      ADD CONSTRAINT uq_clinical_rule_definitions_rule_code UNIQUE (rule_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.clinical_guideline_packs') IS NULL THEN
    RAISE NOTICE 'clinical_guideline_packs missing — skip FK fk_clinical_rule_definitions_pack_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_clinical_rule_definitions_pack_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE clinical_rule_definitions
    ADD CONSTRAINT fk_clinical_rule_definitions_pack_id
    FOREIGN KEY (pack_id) REFERENCES clinical_guideline_packs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_clinical_rule_definitions_pack_id: %', SQLERRM;
END $$;

-- ===== clinical_summaries =====
CREATE TABLE IF NOT EXISTS clinical_summaries (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE clinical_summaries ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE clinical_summaries ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE clinical_summaries ADD COLUMN IF NOT EXISTS risk_level VARCHAR(50) DEFAULT 'LOW';
ALTER TABLE clinical_summaries ADD COLUMN IF NOT EXISTS findings TEXT;
ALTER TABLE clinical_summaries ADD COLUMN IF NOT EXISTS recommendations TEXT;
ALTER TABLE clinical_summaries ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== cold_box_devices =====
CREATE TABLE IF NOT EXISTS cold_box_devices (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE cold_box_devices ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE cold_box_devices ADD COLUMN IF NOT EXISTS device_id VARCHAR(36);
ALTER TABLE cold_box_devices ADD COLUMN IF NOT EXISTS box_code VARCHAR(50);
ALTER TABLE cold_box_devices ADD COLUMN IF NOT EXISTS capacity_liters FLOAT DEFAULT 20;
ALTER TABLE cold_box_devices ADD COLUMN IF NOT EXISTS min_temp_c FLOAT DEFAULT 2.0;
ALTER TABLE cold_box_devices ADD COLUMN IF NOT EXISTS max_temp_c FLOAT DEFAULT 8.0;
ALTER TABLE cold_box_devices ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE cold_box_devices ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_cold_box_devices_device_id ON cold_box_devices (device_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_cold_box_devices_box_code ON cold_box_devices (box_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_cold_box_devices_box_code'
  ) THEN
    ALTER TABLE cold_box_devices
      ADD CONSTRAINT uq_cold_box_devices_box_code UNIQUE (box_code);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_cold_box_devices_device_id'
  ) THEN
    ALTER TABLE cold_box_devices
      ADD CONSTRAINT uq_cold_box_devices_device_id UNIQUE (device_id);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.iot_devices') IS NULL THEN
    RAISE NOTICE 'iot_devices missing — skip FK fk_cold_box_devices_device_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_cold_box_devices_device_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE cold_box_devices
    ADD CONSTRAINT fk_cold_box_devices_device_id
    FOREIGN KEY (device_id) REFERENCES iot_devices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_cold_box_devices_device_id: %', SQLERRM;
END $$;

-- ===== cold_chain_alerts =====
CREATE TABLE IF NOT EXISTS cold_chain_alerts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE cold_chain_alerts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE cold_chain_alerts ADD COLUMN IF NOT EXISTS device_id VARCHAR(36);
ALTER TABLE cold_chain_alerts ADD COLUMN IF NOT EXISTS alert_code VARCHAR(50);
ALTER TABLE cold_chain_alerts ADD COLUMN IF NOT EXISTS alert_type VARCHAR(50);
ALTER TABLE cold_chain_alerts ADD COLUMN IF NOT EXISTS severity VARCHAR(20) DEFAULT 'HIGH';
ALTER TABLE cold_chain_alerts ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE cold_chain_alerts ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'OPEN';
ALTER TABLE cold_chain_alerts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE cold_chain_alerts ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_cold_chain_alerts_alert_code ON cold_chain_alerts (alert_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_cold_chain_alerts_alert_code'
  ) THEN
    ALTER TABLE cold_chain_alerts
      ADD CONSTRAINT uq_cold_chain_alerts_alert_code UNIQUE (alert_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.iot_devices') IS NULL THEN
    RAISE NOTICE 'iot_devices missing — skip FK fk_cold_chain_alerts_device_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_cold_chain_alerts_device_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE cold_chain_alerts
    ADD CONSTRAINT fk_cold_chain_alerts_device_id
    FOREIGN KEY (device_id) REFERENCES iot_devices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_cold_chain_alerts_device_id: %', SQLERRM;
END $$;

-- ===== collector_analytics =====
CREATE TABLE IF NOT EXISTS collector_analytics (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE collector_analytics ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE collector_analytics ADD COLUMN IF NOT EXISTS analytics_code VARCHAR(50);
ALTER TABLE collector_analytics ADD COLUMN IF NOT EXISTS period_start TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_analytics ADD COLUMN IF NOT EXISTS period_end TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_analytics ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE collector_analytics ADD COLUMN IF NOT EXISTS orders_assigned INTEGER DEFAULT 0;
ALTER TABLE collector_analytics ADD COLUMN IF NOT EXISTS orders_completed INTEGER DEFAULT 0;
ALTER TABLE collector_analytics ADD COLUMN IF NOT EXISTS utilization_rate FLOAT DEFAULT 0;
ALTER TABLE collector_analytics ADD COLUMN IF NOT EXISTS transport_time_avg_minutes FLOAT DEFAULT 0;
ALTER TABLE collector_analytics ADD COLUMN IF NOT EXISTS metrics_json TEXT DEFAULT '{}';
ALTER TABLE collector_analytics ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_collector_analytics_analytics_code ON collector_analytics (analytics_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_collector_analytics_analytics_code'
  ) THEN
    ALTER TABLE collector_analytics
      ADD CONSTRAINT uq_collector_analytics_analytics_code UNIQUE (analytics_code);
  END IF;
END $$;


-- ===== collector_availabilities =====
CREATE TABLE IF NOT EXISTS collector_availabilities (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE collector_availabilities ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE collector_availabilities ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE collector_availabilities ADD COLUMN IF NOT EXISTS date VARCHAR(20);
ALTER TABLE collector_availabilities ADD COLUMN IF NOT EXISTS start_time VARCHAR(10);
ALTER TABLE collector_availabilities ADD COLUMN IF NOT EXISTS end_time VARCHAR(10);
ALTER TABLE collector_availabilities ADD COLUMN IF NOT EXISTS district VARCHAR(100);
ALTER TABLE collector_availabilities ADD COLUMN IF NOT EXISTS city VARCHAR(100);
ALTER TABLE collector_availabilities ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'AVAILABLE';
ALTER TABLE collector_availabilities ADD COLUMN IF NOT EXISTS max_jobs INTEGER DEFAULT 8;
ALTER TABLE collector_availabilities ADD COLUMN IF NOT EXISTS assigned_jobs INTEGER DEFAULT 0;
ALTER TABLE collector_availabilities ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_collector_availability_window'
  ) THEN
    ALTER TABLE collector_availabilities
      ADD CONSTRAINT uq_collector_availability_window UNIQUE (collector_id, date, start_time, end_time);
  END IF;
END $$;


-- ===== collector_check_events =====
CREATE TABLE IF NOT EXISTS collector_check_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE collector_check_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE collector_check_events ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE collector_check_events ADD COLUMN IF NOT EXISTS route_id VARCHAR(36);
ALTER TABLE collector_check_events ADD COLUMN IF NOT EXISTS booking_id VARCHAR(36);
ALTER TABLE collector_check_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(50);
ALTER TABLE collector_check_events ADD COLUMN IF NOT EXISTS latitude VARCHAR(50);
ALTER TABLE collector_check_events ADD COLUMN IF NOT EXISTS longitude VARCHAR(50);
ALTER TABLE collector_check_events ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE collector_check_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.collector_routes') IS NULL THEN
    RAISE NOTICE 'collector_routes missing — skip FK fk_collector_check_events_route_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_check_events_route_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_check_events
    ADD CONSTRAINT fk_collector_check_events_route_id
    FOREIGN KEY (route_id) REFERENCES collector_routes (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_check_events_route_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.marketplace_bookings') IS NULL THEN
    RAISE NOTICE 'marketplace_bookings missing — skip FK fk_collector_check_events_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_check_events_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_check_events
    ADD CONSTRAINT fk_collector_check_events_booking_id
    FOREIGN KEY (booking_id) REFERENCES marketplace_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_check_events_booking_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.drivers') IS NULL THEN
    RAISE NOTICE 'drivers missing — skip FK fk_collector_check_events_collector_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_check_events_collector_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_check_events
    ADD CONSTRAINT fk_collector_check_events_collector_id
    FOREIGN KEY (collector_id) REFERENCES drivers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_check_events_collector_id: %', SQLERRM;
END $$;

-- ===== collector_gps_pings =====
CREATE TABLE IF NOT EXISTS collector_gps_pings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE collector_gps_pings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE collector_gps_pings ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE collector_gps_pings ADD COLUMN IF NOT EXISTS route_id VARCHAR(36);
ALTER TABLE collector_gps_pings ADD COLUMN IF NOT EXISTS latitude VARCHAR(50);
ALTER TABLE collector_gps_pings ADD COLUMN IF NOT EXISTS longitude VARCHAR(50);
ALTER TABLE collector_gps_pings ADD COLUMN IF NOT EXISTS speed_kmh FLOAT;
ALTER TABLE collector_gps_pings ADD COLUMN IF NOT EXISTS heading FLOAT;
ALTER TABLE collector_gps_pings ADD COLUMN IF NOT EXISTS accuracy_m FLOAT;
ALTER TABLE collector_gps_pings ADD COLUMN IF NOT EXISTS recorded_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_gps_pings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.collector_routes') IS NULL THEN
    RAISE NOTICE 'collector_routes missing — skip FK fk_collector_gps_pings_route_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_gps_pings_route_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_gps_pings
    ADD CONSTRAINT fk_collector_gps_pings_route_id
    FOREIGN KEY (route_id) REFERENCES collector_routes (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_gps_pings_route_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.drivers') IS NULL THEN
    RAISE NOTICE 'drivers missing — skip FK fk_collector_gps_pings_collector_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_gps_pings_collector_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_gps_pings
    ADD CONSTRAINT fk_collector_gps_pings_collector_id
    FOREIGN KEY (collector_id) REFERENCES drivers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_gps_pings_collector_id: %', SQLERRM;
END $$;

-- ===== collector_handovers =====
CREATE TABLE IF NOT EXISTS collector_handovers (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS handover_type VARCHAR(50);
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS object_code VARCHAR(100);
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS qr_payload VARCHAR(255);
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS booking_id VARCHAR(36);
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS sample_tracking_id VARCHAR(36);
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS transport_box_id VARCHAR(36);
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS shipment_id VARCHAR(36);
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS recipient_name VARCHAR(255);
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS latitude VARCHAR(50);
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS longitude VARCHAR(50);
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE collector_handovers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.drivers') IS NULL THEN
    RAISE NOTICE 'drivers missing — skip FK fk_collector_handovers_collector_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_handovers_collector_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_handovers
    ADD CONSTRAINT fk_collector_handovers_collector_id
    FOREIGN KEY (collector_id) REFERENCES drivers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_handovers_collector_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.marketplace_bookings') IS NULL THEN
    RAISE NOTICE 'marketplace_bookings missing — skip FK fk_collector_handovers_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_handovers_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_handovers
    ADD CONSTRAINT fk_collector_handovers_booking_id
    FOREIGN KEY (booking_id) REFERENCES marketplace_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_handovers_booking_id: %', SQLERRM;
END $$;

-- ===== collector_offline_syncs =====
CREATE TABLE IF NOT EXISTS collector_offline_syncs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE collector_offline_syncs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE collector_offline_syncs ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE collector_offline_syncs ADD COLUMN IF NOT EXISTS client_event_id VARCHAR(100);
ALTER TABLE collector_offline_syncs ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE collector_offline_syncs ADD COLUMN IF NOT EXISTS payload_json TEXT;
ALTER TABLE collector_offline_syncs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE collector_offline_syncs ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE collector_offline_syncs ADD COLUMN IF NOT EXISTS client_recorded_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_offline_syncs ADD COLUMN IF NOT EXISTS synced_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_offline_syncs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.drivers') IS NULL THEN
    RAISE NOTICE 'drivers missing — skip FK fk_collector_offline_syncs_collector_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_offline_syncs_collector_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_offline_syncs
    ADD CONSTRAINT fk_collector_offline_syncs_collector_id
    FOREIGN KEY (collector_id) REFERENCES drivers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_offline_syncs_collector_id: %', SQLERRM;
END $$;

-- ===== collector_operation_timelines =====
CREATE TABLE IF NOT EXISTS collector_operation_timelines (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE collector_operation_timelines ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE collector_operation_timelines ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE collector_operation_timelines ADD COLUMN IF NOT EXISTS route_id VARCHAR(36);
ALTER TABLE collector_operation_timelines ADD COLUMN IF NOT EXISTS booking_id VARCHAR(36);
ALTER TABLE collector_operation_timelines ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE collector_operation_timelines ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE collector_operation_timelines ADD COLUMN IF NOT EXISTS actor_email VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE collector_operation_timelines ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE collector_operation_timelines ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.drivers') IS NULL THEN
    RAISE NOTICE 'drivers missing — skip FK fk_collector_operation_timelines_collector_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_operation_timelines_collector_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_operation_timelines
    ADD CONSTRAINT fk_collector_operation_timelines_collector_id
    FOREIGN KEY (collector_id) REFERENCES drivers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_operation_timelines_collector_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.marketplace_bookings') IS NULL THEN
    RAISE NOTICE 'marketplace_bookings missing — skip FK fk_collector_operation_timelines_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_operation_timelines_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_operation_timelines
    ADD CONSTRAINT fk_collector_operation_timelines_booking_id
    FOREIGN KEY (booking_id) REFERENCES marketplace_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_operation_timelines_booking_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.collector_routes') IS NULL THEN
    RAISE NOTICE 'collector_routes missing — skip FK fk_collector_operation_timelines_route_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_operation_timelines_route_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_operation_timelines
    ADD CONSTRAINT fk_collector_operation_timelines_route_id
    FOREIGN KEY (route_id) REFERENCES collector_routes (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_operation_timelines_route_id: %', SQLERRM;
END $$;

-- ===== collector_payouts =====
CREATE TABLE IF NOT EXISTS collector_payouts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE collector_payouts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE collector_payouts ADD COLUMN IF NOT EXISTS payout_code VARCHAR(50);
ALTER TABLE collector_payouts ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE collector_payouts ADD COLUMN IF NOT EXISTS settlement_id VARCHAR(36);
ALTER TABLE collector_payouts ADD COLUMN IF NOT EXISTS amount FLOAT DEFAULT 0;
ALTER TABLE collector_payouts ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE collector_payouts ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_payouts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_collector_payouts_payout_code ON collector_payouts (payout_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_collector_payouts_payout_code'
  ) THEN
    ALTER TABLE collector_payouts
      ADD CONSTRAINT uq_collector_payouts_payout_code UNIQUE (payout_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.partner_settlements') IS NULL THEN
    RAISE NOTICE 'partner_settlements missing — skip FK fk_collector_payouts_settlement_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_payouts_settlement_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_payouts
    ADD CONSTRAINT fk_collector_payouts_settlement_id
    FOREIGN KEY (settlement_id) REFERENCES partner_settlements (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_payouts_settlement_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.drivers') IS NULL THEN
    RAISE NOTICE 'drivers missing — skip FK fk_collector_payouts_collector_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_payouts_collector_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_payouts
    ADD CONSTRAINT fk_collector_payouts_collector_id
    FOREIGN KEY (collector_id) REFERENCES drivers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_payouts_collector_id: %', SQLERRM;
END $$;

-- ===== collector_proofs =====
CREATE TABLE IF NOT EXISTS collector_proofs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE collector_proofs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE collector_proofs ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE collector_proofs ADD COLUMN IF NOT EXISTS proof_type VARCHAR(50);
ALTER TABLE collector_proofs ADD COLUMN IF NOT EXISTS booking_id VARCHAR(36);
ALTER TABLE collector_proofs ADD COLUMN IF NOT EXISTS route_stop_id VARCHAR(36);
ALTER TABLE collector_proofs ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);
ALTER TABLE collector_proofs ADD COLUMN IF NOT EXISTS content_base64 TEXT;
ALTER TABLE collector_proofs ADD COLUMN IF NOT EXISTS signer_name VARCHAR(255);
ALTER TABLE collector_proofs ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE collector_proofs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.marketplace_bookings') IS NULL THEN
    RAISE NOTICE 'marketplace_bookings missing — skip FK fk_collector_proofs_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_proofs_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_proofs
    ADD CONSTRAINT fk_collector_proofs_booking_id
    FOREIGN KEY (booking_id) REFERENCES marketplace_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_proofs_booking_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.collector_route_stops') IS NULL THEN
    RAISE NOTICE 'collector_route_stops missing — skip FK fk_collector_proofs_route_stop_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_proofs_route_stop_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_proofs
    ADD CONSTRAINT fk_collector_proofs_route_stop_id
    FOREIGN KEY (route_stop_id) REFERENCES collector_route_stops (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_proofs_route_stop_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.drivers') IS NULL THEN
    RAISE NOTICE 'drivers missing — skip FK fk_collector_proofs_collector_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_proofs_collector_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_proofs
    ADD CONSTRAINT fk_collector_proofs_collector_id
    FOREIGN KEY (collector_id) REFERENCES drivers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_proofs_collector_id: %', SQLERRM;
END $$;

-- ===== collector_route_stops =====
CREATE TABLE IF NOT EXISTS collector_route_stops (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS route_id VARCHAR(36);
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS booking_id VARCHAR(36);
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS assignment_id VARCHAR(36);
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS sequence_no INTEGER DEFAULT 1;
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS patient_name VARCHAR(255);
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS latitude VARCHAR(50);
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS longitude VARCHAR(50);
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS estimated_arrival VARCHAR(20);
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS arrived_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_route_stops ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.collector_routes') IS NULL THEN
    RAISE NOTICE 'collector_routes missing — skip FK fk_collector_route_stops_route_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_route_stops_route_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_route_stops
    ADD CONSTRAINT fk_collector_route_stops_route_id
    FOREIGN KEY (route_id) REFERENCES collector_routes (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_route_stops_route_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.booking_assignments') IS NULL THEN
    RAISE NOTICE 'booking_assignments missing — skip FK fk_collector_route_stops_assignment_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_route_stops_assignment_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_route_stops
    ADD CONSTRAINT fk_collector_route_stops_assignment_id
    FOREIGN KEY (assignment_id) REFERENCES booking_assignments (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_route_stops_assignment_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.marketplace_bookings') IS NULL THEN
    RAISE NOTICE 'marketplace_bookings missing — skip FK fk_collector_route_stops_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_route_stops_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_route_stops
    ADD CONSTRAINT fk_collector_route_stops_booking_id
    FOREIGN KEY (booking_id) REFERENCES marketplace_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_route_stops_booking_id: %', SQLERRM;
END $$;

-- ===== collector_routes =====
CREATE TABLE IF NOT EXISTS collector_routes (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS route_code VARCHAR(50);
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS vehicle_id VARCHAR(36);
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS transport_box_id VARCHAR(36);
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PLANNED';
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS total_stops INTEGER DEFAULT 0;
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS completed_stops INTEGER DEFAULT 0;
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS total_distance_km FLOAT DEFAULT 0;
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS estimated_minutes INTEGER DEFAULT 0;
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS route_score FLOAT DEFAULT 100;
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS start_latitude VARCHAR(50);
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS start_longitude VARCHAR(50);
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS optimized_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_routes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_collector_routes_route_code ON collector_routes (route_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_collector_routes_route_code'
  ) THEN
    ALTER TABLE collector_routes
      ADD CONSTRAINT uq_collector_routes_route_code UNIQUE (route_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.drivers') IS NULL THEN
    RAISE NOTICE 'drivers missing — skip FK fk_collector_routes_collector_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_routes_collector_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_routes
    ADD CONSTRAINT fk_collector_routes_collector_id
    FOREIGN KEY (collector_id) REFERENCES drivers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_routes_collector_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.collector_vehicles') IS NULL THEN
    RAISE NOTICE 'collector_vehicles missing — skip FK fk_collector_routes_vehicle_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_routes_vehicle_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_routes
    ADD CONSTRAINT fk_collector_routes_vehicle_id
    FOREIGN KEY (vehicle_id) REFERENCES collector_vehicles (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_routes_vehicle_id: %', SQLERRM;
END $$;

-- ===== collector_vehicles =====
CREATE TABLE IF NOT EXISTS collector_vehicles (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE collector_vehicles ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE collector_vehicles ADD COLUMN IF NOT EXISTS vehicle_code VARCHAR(50);
ALTER TABLE collector_vehicles ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE collector_vehicles ADD COLUMN IF NOT EXISTS plate_number VARCHAR(50);
ALTER TABLE collector_vehicles ADD COLUMN IF NOT EXISTS vehicle_type VARCHAR(50) DEFAULT 'MOTORBIKE';
ALTER TABLE collector_vehicles ADD COLUMN IF NOT EXISTS brand VARCHAR(100);
ALTER TABLE collector_vehicles ADD COLUMN IF NOT EXISTS model VARCHAR(100);
ALTER TABLE collector_vehicles ADD COLUMN IF NOT EXISTS capacity_boxes INTEGER DEFAULT 1;
ALTER TABLE collector_vehicles ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE collector_vehicles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE collector_vehicles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_collector_vehicles_vehicle_code ON collector_vehicles (vehicle_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_collector_vehicles_vehicle_code'
  ) THEN
    ALTER TABLE collector_vehicles
      ADD CONSTRAINT uq_collector_vehicles_vehicle_code UNIQUE (vehicle_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.drivers') IS NULL THEN
    RAISE NOTICE 'drivers missing — skip FK fk_collector_vehicles_collector_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_collector_vehicles_collector_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE collector_vehicles
    ADD CONSTRAINT fk_collector_vehicles_collector_id
    FOREIGN KEY (collector_id) REFERENCES drivers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_collector_vehicles_collector_id: %', SQLERRM;
END $$;

-- ===== commission_ledger =====
CREATE TABLE IF NOT EXISTS commission_ledger (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE commission_ledger ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE commission_ledger ADD COLUMN IF NOT EXISTS ledger_code VARCHAR(50);
ALTER TABLE commission_ledger ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE commission_ledger ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE commission_ledger ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE commission_ledger ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE commission_ledger ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE commission_ledger ADD COLUMN IF NOT EXISTS role_type VARCHAR(50);
ALTER TABLE commission_ledger ADD COLUMN IF NOT EXISTS gross_amount FLOAT DEFAULT 0;
ALTER TABLE commission_ledger ADD COLUMN IF NOT EXISTS commission_amount FLOAT DEFAULT 0;
ALTER TABLE commission_ledger ADD COLUMN IF NOT EXISTS rule_id VARCHAR(36);
ALTER TABLE commission_ledger ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_commission_ledger_ledger_code ON commission_ledger (ledger_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_commission_ledger_ledger_code'
  ) THEN
    ALTER TABLE commission_ledger
      ADD CONSTRAINT uq_commission_ledger_ledger_code UNIQUE (ledger_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_commission_ledger_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_commission_ledger_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE commission_ledger
    ADD CONSTRAINT fk_commission_ledger_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_commission_ledger_medical_order_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_commission_ledger_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_commission_ledger_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE commission_ledger
    ADD CONSTRAINT fk_commission_ledger_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_commission_ledger_partner_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.invoices') IS NULL THEN
    RAISE NOTICE 'invoices missing — skip FK fk_commission_ledger_invoice_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_commission_ledger_invoice_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE commission_ledger
    ADD CONSTRAINT fk_commission_ledger_invoice_id
    FOREIGN KEY (invoice_id) REFERENCES invoices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_commission_ledger_invoice_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.commission_rules') IS NULL THEN
    RAISE NOTICE 'commission_rules missing — skip FK fk_commission_ledger_rule_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_commission_ledger_rule_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE commission_ledger
    ADD CONSTRAINT fk_commission_ledger_rule_id
    FOREIGN KEY (rule_id) REFERENCES commission_rules (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_commission_ledger_rule_id: %', SQLERRM;
END $$;

-- ===== commission_rules =====
CREATE TABLE IF NOT EXISTS commission_rules (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE commission_rules ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE commission_rules ADD COLUMN IF NOT EXISTS rule_code VARCHAR(50);
ALTER TABLE commission_rules ADD COLUMN IF NOT EXISTS partner_type VARCHAR(50);
ALTER TABLE commission_rules ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE commission_rules ADD COLUMN IF NOT EXISTS role_type VARCHAR(50) DEFAULT 'PARTNER';
ALTER TABLE commission_rules ADD COLUMN IF NOT EXISTS rate_percent FLOAT DEFAULT 0;
ALTER TABLE commission_rules ADD COLUMN IF NOT EXISTS flat_fee FLOAT DEFAULT 0;
ALTER TABLE commission_rules ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE commission_rules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_commission_rules_rule_code ON commission_rules (rule_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_commission_rules_rule_code'
  ) THEN
    ALTER TABLE commission_rules
      ADD CONSTRAINT uq_commission_rules_rule_code UNIQUE (rule_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_commission_rules_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_commission_rules_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE commission_rules
    ADD CONSTRAINT fk_commission_rules_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_commission_rules_partner_id: %', SQLERRM;
END $$;

-- ===== communication_dead_letters =====
CREATE TABLE IF NOT EXISTS communication_dead_letters (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE communication_dead_letters ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE communication_dead_letters ADD COLUMN IF NOT EXISTS dead_letter_code VARCHAR(50);
ALTER TABLE communication_dead_letters ADD COLUMN IF NOT EXISTS queue_item_id VARCHAR(36);
ALTER TABLE communication_dead_letters ADD COLUMN IF NOT EXISTS channel VARCHAR(50);
ALTER TABLE communication_dead_letters ADD COLUMN IF NOT EXISTS reason TEXT;
ALTER TABLE communication_dead_letters ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE communication_dead_letters ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_communication_dead_letters_dead_letter_code ON communication_dead_letters (dead_letter_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_communication_dead_letters_dead_letter_code'
  ) THEN
    ALTER TABLE communication_dead_letters
      ADD CONSTRAINT uq_communication_dead_letters_dead_letter_code UNIQUE (dead_letter_code);
  END IF;
END $$;


-- ===== communication_delivery_tracks =====
CREATE TABLE IF NOT EXISTS communication_delivery_tracks (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE communication_delivery_tracks ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE communication_delivery_tracks ADD COLUMN IF NOT EXISTS track_code VARCHAR(50);
ALTER TABLE communication_delivery_tracks ADD COLUMN IF NOT EXISTS queue_item_id VARCHAR(36);
ALTER TABLE communication_delivery_tracks ADD COLUMN IF NOT EXISTS notification_id VARCHAR(36);
ALTER TABLE communication_delivery_tracks ADD COLUMN IF NOT EXISTS channel VARCHAR(50);
ALTER TABLE communication_delivery_tracks ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE communication_delivery_tracks ADD COLUMN IF NOT EXISTS provider_message_id VARCHAR(100);
ALTER TABLE communication_delivery_tracks ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE communication_delivery_tracks ADD COLUMN IF NOT EXISTS sent_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE communication_delivery_tracks ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE communication_delivery_tracks ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_communication_delivery_tracks_track_code ON communication_delivery_tracks (track_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_communication_delivery_tracks_track_code'
  ) THEN
    ALTER TABLE communication_delivery_tracks
      ADD CONSTRAINT uq_communication_delivery_tracks_track_code UNIQUE (track_code);
  END IF;
END $$;


-- ===== communication_queue_items =====
CREATE TABLE IF NOT EXISTS communication_queue_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS queue_code VARCHAR(50);
ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS channel VARCHAR(50);
ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS template_code VARCHAR(50);
ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS recipient VARCHAR(255);
ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3;
ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS notification_id VARCHAR(36);
ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE communication_queue_items ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_communication_queue_items_queue_code ON communication_queue_items (queue_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_communication_queue_items_queue_code'
  ) THEN
    ALTER TABLE communication_queue_items
      ADD CONSTRAINT uq_communication_queue_items_queue_code UNIQUE (queue_code);
  END IF;
END $$;


-- ===== companies =====
CREATE TABLE IF NOT EXISTS companies (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE companies ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS company_code VARCHAR(50);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS tax_code VARCHAR(50);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS contact_person VARCHAR(255);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE companies ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_companies_company_code ON companies (company_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_companies_company_code'
  ) THEN
    ALTER TABLE companies
      ADD CONSTRAINT uq_companies_company_code UNIQUE (company_code);
  END IF;
END $$;


-- ===== contract_prices =====
CREATE TABLE IF NOT EXISTS contract_prices (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE contract_prices ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE contract_prices ADD COLUMN IF NOT EXISTS contract_id VARCHAR(36);
ALTER TABLE contract_prices ADD COLUMN IF NOT EXISTS test_catalog_id VARCHAR(36);
ALTER TABLE contract_prices ADD COLUMN IF NOT EXISTS standard_price FLOAT DEFAULT 0;
ALTER TABLE contract_prices ADD COLUMN IF NOT EXISTS contract_price FLOAT DEFAULT 0;
ALTER TABLE contract_prices ADD COLUMN IF NOT EXISTS discount_percent FLOAT DEFAULT 0;
ALTER TABLE contract_prices ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== contracts =====
CREATE TABLE IF NOT EXISTS contracts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE contracts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS contract_code VARCHAR(50);
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS company_id VARCHAR(36);
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS contract_type VARCHAR(100) DEFAULT 'SERVICE';
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS start_date VARCHAR(20);
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS end_date VARCHAR(20);
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS total_value FLOAT DEFAULT 0;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_contracts_contract_code ON contracts (contract_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_contracts_contract_code'
  ) THEN
    ALTER TABLE contracts
      ADD CONSTRAINT uq_contracts_contract_code UNIQUE (contract_code);
  END IF;
END $$;


-- ===== critical_alert_events =====
CREATE TABLE IF NOT EXISTS critical_alert_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE critical_alert_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE critical_alert_events ADD COLUMN IF NOT EXISTS alert_code VARCHAR(50);
ALTER TABLE critical_alert_events ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE critical_alert_events ADD COLUMN IF NOT EXISTS patient_id VARCHAR(36);
ALTER TABLE critical_alert_events ADD COLUMN IF NOT EXISTS alert_type VARCHAR(50);
ALTER TABLE critical_alert_events ADD COLUMN IF NOT EXISTS severity VARCHAR(20) DEFAULT 'CRITICAL';
ALTER TABLE critical_alert_events ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE critical_alert_events ADD COLUMN IF NOT EXISTS markers_json TEXT DEFAULT '[]';
ALTER TABLE critical_alert_events ADD COLUMN IF NOT EXISTS notification_status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE critical_alert_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_critical_alert_events_alert_code ON critical_alert_events (alert_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_critical_alert_events_alert_code'
  ) THEN
    ALTER TABLE critical_alert_events
      ADD CONSTRAINT uq_critical_alert_events_alert_code UNIQUE (alert_code);
  END IF;
END $$;


-- ===== critical_result_alerts =====
CREATE TABLE IF NOT EXISTS critical_result_alerts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE critical_result_alerts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE critical_result_alerts ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE critical_result_alerts ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE critical_result_alerts ADD COLUMN IF NOT EXISTS order_code VARCHAR(50);
ALTER TABLE critical_result_alerts ADD COLUMN IF NOT EXISTS result_id VARCHAR(36);
ALTER TABLE critical_result_alerts ADD COLUMN IF NOT EXISTS report_id VARCHAR(36);
ALTER TABLE critical_result_alerts ADD COLUMN IF NOT EXISTS critical_type VARCHAR(50);
ALTER TABLE critical_result_alerts ADD COLUMN IF NOT EXISTS acknowledged_by VARCHAR(255);
ALTER TABLE critical_result_alerts ADD COLUMN IF NOT EXISTS acknowledged_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE critical_result_alerts ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'new';
ALTER TABLE critical_result_alerts ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE critical_result_alerts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_critical_result_alerts_patient_id ON critical_result_alerts (patient_id);
CREATE INDEX IF NOT EXISTS ix_critical_result_alerts_status ON critical_result_alerts (status);



-- ===== critical_value_rules =====
CREATE TABLE IF NOT EXISTS critical_value_rules (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE critical_value_rules ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE critical_value_rules ADD COLUMN IF NOT EXISTS rule_code VARCHAR(50);
ALTER TABLE critical_value_rules ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE critical_value_rules ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE critical_value_rules ADD COLUMN IF NOT EXISTS panic_low FLOAT;
ALTER TABLE critical_value_rules ADD COLUMN IF NOT EXISTS panic_high FLOAT;
ALTER TABLE critical_value_rules ADD COLUMN IF NOT EXISTS severity VARCHAR(20) DEFAULT 'CRITICAL';
ALTER TABLE critical_value_rules ADD COLUMN IF NOT EXISTS message_en TEXT;
ALTER TABLE critical_value_rules ADD COLUMN IF NOT EXISTS message_vi TEXT;
ALTER TABLE critical_value_rules ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE critical_value_rules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_critical_value_rules_rule_code ON critical_value_rules (rule_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_critical_value_rules_rule_code'
  ) THEN
    ALTER TABLE critical_value_rules
      ADD CONSTRAINT uq_critical_value_rules_rule_code UNIQUE (rule_code);
  END IF;
END $$;


-- ===== crm_activities =====
CREATE TABLE IF NOT EXISTS crm_activities (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS activity_type VARCHAR(50);
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS subject VARCHAR(255);
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS related_type VARCHAR(50);
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS related_id VARCHAR(36);
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS lead_id VARCHAR(36);
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS customer_id VARCHAR(36);
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS opportunity_id VARCHAR(36);
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS due_date TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS reminder_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS is_completed BOOLEAN DEFAULT FALSE;
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS attachment_url VARCHAR(500);
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS owner VARCHAR(255);
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE crm_activities ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.crm_customers') IS NULL THEN
    RAISE NOTICE 'crm_customers missing — skip FK fk_crm_activities_customer_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_activities_customer_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_activities
    ADD CONSTRAINT fk_crm_activities_customer_id
    FOREIGN KEY (customer_id) REFERENCES crm_customers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_activities_customer_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.crm_opportunities') IS NULL THEN
    RAISE NOTICE 'crm_opportunities missing — skip FK fk_crm_activities_opportunity_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_activities_opportunity_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_activities
    ADD CONSTRAINT fk_crm_activities_opportunity_id
    FOREIGN KEY (opportunity_id) REFERENCES crm_opportunities (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_activities_opportunity_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.crm_leads') IS NULL THEN
    RAISE NOTICE 'crm_leads missing — skip FK fk_crm_activities_lead_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_activities_lead_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_activities
    ADD CONSTRAINT fk_crm_activities_lead_id
    FOREIGN KEY (lead_id) REFERENCES crm_leads (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_activities_lead_id: %', SQLERRM;
END $$;

-- ===== crm_contact_persons =====
CREATE TABLE IF NOT EXISTS crm_contact_persons (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_contact_persons ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_contact_persons ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE crm_contact_persons ADD COLUMN IF NOT EXISTS customer_id VARCHAR(36);
ALTER TABLE crm_contact_persons ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE crm_contact_persons ADD COLUMN IF NOT EXISTS title VARCHAR(100);
ALTER TABLE crm_contact_persons ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE crm_contact_persons ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE crm_contact_persons ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT FALSE;
ALTER TABLE crm_contact_persons ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.crm_organizations') IS NULL THEN
    RAISE NOTICE 'crm_organizations missing — skip FK fk_crm_contact_persons_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_contact_persons_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_contact_persons
    ADD CONSTRAINT fk_crm_contact_persons_organization_id
    FOREIGN KEY (organization_id) REFERENCES crm_organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_contact_persons_organization_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.crm_customers') IS NULL THEN
    RAISE NOTICE 'crm_customers missing — skip FK fk_crm_contact_persons_customer_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_contact_persons_customer_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_contact_persons
    ADD CONSTRAINT fk_crm_contact_persons_customer_id
    FOREIGN KEY (customer_id) REFERENCES crm_customers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_contact_persons_customer_id: %', SQLERRM;
END $$;

-- ===== crm_customers =====
CREATE TABLE IF NOT EXISTS crm_customers (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_customers ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_customers ADD COLUMN IF NOT EXISTS customer_code VARCHAR(50);
ALTER TABLE crm_customers ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE crm_customers ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE crm_customers ADD COLUMN IF NOT EXISTS customer_type VARCHAR(50) DEFAULT 'B2B';
ALTER TABLE crm_customers ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE crm_customers ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE crm_customers ADD COLUMN IF NOT EXISTS billing_address VARCHAR(500);
ALTER TABLE crm_customers ADD COLUMN IF NOT EXISTS owner VARCHAR(255);
ALTER TABLE crm_customers ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE crm_customers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE crm_customers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_crm_customers_customer_code ON crm_customers (customer_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_crm_customers_customer_code'
  ) THEN
    ALTER TABLE crm_customers
      ADD CONSTRAINT uq_crm_customers_customer_code UNIQUE (customer_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.crm_organizations') IS NULL THEN
    RAISE NOTICE 'crm_organizations missing — skip FK fk_crm_customers_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_customers_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_customers
    ADD CONSTRAINT fk_crm_customers_organization_id
    FOREIGN KEY (organization_id) REFERENCES crm_organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_customers_organization_id: %', SQLERRM;
END $$;

-- ===== crm_discount_rules =====
CREATE TABLE IF NOT EXISTS crm_discount_rules (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_discount_rules ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_discount_rules ADD COLUMN IF NOT EXISTS rule_code VARCHAR(50);
ALTER TABLE crm_discount_rules ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE crm_discount_rules ADD COLUMN IF NOT EXISTS discount_percent FLOAT DEFAULT 0;
ALTER TABLE crm_discount_rules ADD COLUMN IF NOT EXISTS min_amount FLOAT DEFAULT 0;
ALTER TABLE crm_discount_rules ADD COLUMN IF NOT EXISTS customer_id VARCHAR(36);
ALTER TABLE crm_discount_rules ADD COLUMN IF NOT EXISTS contract_id VARCHAR(36);
ALTER TABLE crm_discount_rules ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE crm_discount_rules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_crm_discount_rules_rule_code ON crm_discount_rules (rule_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_crm_discount_rules_rule_code'
  ) THEN
    ALTER TABLE crm_discount_rules
      ADD CONSTRAINT uq_crm_discount_rules_rule_code UNIQUE (rule_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.crm_customers') IS NULL THEN
    RAISE NOTICE 'crm_customers missing — skip FK fk_crm_discount_rules_customer_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_discount_rules_customer_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_discount_rules
    ADD CONSTRAINT fk_crm_discount_rules_customer_id
    FOREIGN KEY (customer_id) REFERENCES crm_customers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_discount_rules_customer_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.crm_sales_contracts') IS NULL THEN
    RAISE NOTICE 'crm_sales_contracts missing — skip FK fk_crm_discount_rules_contract_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_discount_rules_contract_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_discount_rules
    ADD CONSTRAINT fk_crm_discount_rules_contract_id
    FOREIGN KEY (contract_id) REFERENCES crm_sales_contracts (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_discount_rules_contract_id: %', SQLERRM;
END $$;

-- ===== crm_leads =====
CREATE TABLE IF NOT EXISTS crm_leads (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS lead_code VARCHAR(50);
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS company_name VARCHAR(255);
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS contact_person VARCHAR(255);
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS lead_source VARCHAR(100);
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS pipeline_stage VARCHAR(50) DEFAULT 'LEAD';
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'NEW';
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS estimated_revenue FLOAT DEFAULT 0;
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS owner VARCHAR(255);
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE crm_leads ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_crm_leads_lead_code ON crm_leads (lead_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_crm_leads_lead_code'
  ) THEN
    ALTER TABLE crm_leads
      ADD CONSTRAINT uq_crm_leads_lead_code UNIQUE (lead_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.crm_organizations') IS NULL THEN
    RAISE NOTICE 'crm_organizations missing — skip FK fk_crm_leads_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_leads_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_leads
    ADD CONSTRAINT fk_crm_leads_organization_id
    FOREIGN KEY (organization_id) REFERENCES crm_organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_leads_organization_id: %', SQLERRM;
END $$;

-- ===== crm_opportunities =====
CREATE TABLE IF NOT EXISTS crm_opportunities (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS opportunity_code VARCHAR(50);
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS lead_id VARCHAR(36);
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS customer_id VARCHAR(36);
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS pipeline_id VARCHAR(36);
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS pipeline_stage VARCHAR(50) DEFAULT 'LEAD';
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS amount FLOAT DEFAULT 0;
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'VND';
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS expected_close_date DATE;
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'OPEN';
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS owner VARCHAR(255);
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE crm_opportunities ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_crm_opportunities_opportunity_code ON crm_opportunities (opportunity_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_crm_opportunities_opportunity_code'
  ) THEN
    ALTER TABLE crm_opportunities
      ADD CONSTRAINT uq_crm_opportunities_opportunity_code UNIQUE (opportunity_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.crm_organizations') IS NULL THEN
    RAISE NOTICE 'crm_organizations missing — skip FK fk_crm_opportunities_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_opportunities_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_opportunities
    ADD CONSTRAINT fk_crm_opportunities_organization_id
    FOREIGN KEY (organization_id) REFERENCES crm_organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_opportunities_organization_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.crm_leads') IS NULL THEN
    RAISE NOTICE 'crm_leads missing — skip FK fk_crm_opportunities_lead_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_opportunities_lead_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_opportunities
    ADD CONSTRAINT fk_crm_opportunities_lead_id
    FOREIGN KEY (lead_id) REFERENCES crm_leads (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_opportunities_lead_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.crm_customers') IS NULL THEN
    RAISE NOTICE 'crm_customers missing — skip FK fk_crm_opportunities_customer_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_opportunities_customer_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_opportunities
    ADD CONSTRAINT fk_crm_opportunities_customer_id
    FOREIGN KEY (customer_id) REFERENCES crm_customers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_opportunities_customer_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.crm_sales_pipelines') IS NULL THEN
    RAISE NOTICE 'crm_sales_pipelines missing — skip FK fk_crm_opportunities_pipeline_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_opportunities_pipeline_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_opportunities
    ADD CONSTRAINT fk_crm_opportunities_pipeline_id
    FOREIGN KEY (pipeline_id) REFERENCES crm_sales_pipelines (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_opportunities_pipeline_id: %', SQLERRM;
END $$;

-- ===== crm_organizations =====
CREATE TABLE IF NOT EXISTS crm_organizations (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS org_code VARCHAR(50);
ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS org_type VARCHAR(50) DEFAULT 'CORPORATE';
ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS industry VARCHAR(100);
ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS tax_code VARCHAR(50);
ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS address VARCHAR(500);
ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS owner VARCHAR(255);
ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE crm_organizations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_crm_organizations_org_code ON crm_organizations (org_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_crm_organizations_org_code'
  ) THEN
    ALTER TABLE crm_organizations
      ADD CONSTRAINT uq_crm_organizations_org_code UNIQUE (org_code);
  END IF;
END $$;


-- ===== crm_pipeline_stages =====
CREATE TABLE IF NOT EXISTS crm_pipeline_stages (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_pipeline_stages ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_pipeline_stages ADD COLUMN IF NOT EXISTS pipeline_id VARCHAR(36);
ALTER TABLE crm_pipeline_stages ADD COLUMN IF NOT EXISTS stage_code VARCHAR(50);
ALTER TABLE crm_pipeline_stages ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE crm_pipeline_stages ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;
ALTER TABLE crm_pipeline_stages ADD COLUMN IF NOT EXISTS win_probability FLOAT DEFAULT 0;
ALTER TABLE crm_pipeline_stages ADD COLUMN IF NOT EXISTS is_closed BOOLEAN DEFAULT FALSE;
ALTER TABLE crm_pipeline_stages ADD COLUMN IF NOT EXISTS is_won BOOLEAN DEFAULT FALSE;



DO $$
BEGIN
  IF to_regclass('public.crm_sales_pipelines') IS NULL THEN
    RAISE NOTICE 'crm_sales_pipelines missing — skip FK fk_crm_pipeline_stages_pipeline_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_pipeline_stages_pipeline_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_pipeline_stages
    ADD CONSTRAINT fk_crm_pipeline_stages_pipeline_id
    FOREIGN KEY (pipeline_id) REFERENCES crm_sales_pipelines (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_pipeline_stages_pipeline_id: %', SQLERRM;
END $$;

-- ===== crm_price_books =====
CREATE TABLE IF NOT EXISTS crm_price_books (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_price_books ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_price_books ADD COLUMN IF NOT EXISTS price_book_code VARCHAR(50);
ALTER TABLE crm_price_books ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE crm_price_books ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) DEFAULT 'CATALOG';
ALTER TABLE crm_price_books ADD COLUMN IF NOT EXISTS customer_id VARCHAR(36);
ALTER TABLE crm_price_books ADD COLUMN IF NOT EXISTS contract_id VARCHAR(36);
ALTER TABLE crm_price_books ADD COLUMN IF NOT EXISTS test_catalog_id VARCHAR(36);
ALTER TABLE crm_price_books ADD COLUMN IF NOT EXISTS unit_price FLOAT DEFAULT 0;
ALTER TABLE crm_price_books ADD COLUMN IF NOT EXISTS discount_percent FLOAT DEFAULT 0;
ALTER TABLE crm_price_books ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'VND';
ALTER TABLE crm_price_books ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE crm_price_books ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_crm_price_books_price_book_code ON crm_price_books (price_book_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_crm_price_books_price_book_code'
  ) THEN
    ALTER TABLE crm_price_books
      ADD CONSTRAINT uq_crm_price_books_price_book_code UNIQUE (price_book_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.crm_customers') IS NULL THEN
    RAISE NOTICE 'crm_customers missing — skip FK fk_crm_price_books_customer_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_price_books_customer_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_price_books
    ADD CONSTRAINT fk_crm_price_books_customer_id
    FOREIGN KEY (customer_id) REFERENCES crm_customers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_price_books_customer_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.crm_sales_contracts') IS NULL THEN
    RAISE NOTICE 'crm_sales_contracts missing — skip FK fk_crm_price_books_contract_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_price_books_contract_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_price_books
    ADD CONSTRAINT fk_crm_price_books_contract_id
    FOREIGN KEY (contract_id) REFERENCES crm_sales_contracts (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_price_books_contract_id: %', SQLERRM;
END $$;

-- ===== crm_quotation_items =====
CREATE TABLE IF NOT EXISTS crm_quotation_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_quotation_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_quotation_items ADD COLUMN IF NOT EXISTS quotation_id VARCHAR(36);
ALTER TABLE crm_quotation_items ADD COLUMN IF NOT EXISTS test_catalog_id VARCHAR(36);
ALTER TABLE crm_quotation_items ADD COLUMN IF NOT EXISTS item_code VARCHAR(50);
ALTER TABLE crm_quotation_items ADD COLUMN IF NOT EXISTS item_name VARCHAR(255);
ALTER TABLE crm_quotation_items ADD COLUMN IF NOT EXISTS quantity INTEGER DEFAULT 1;
ALTER TABLE crm_quotation_items ADD COLUMN IF NOT EXISTS unit_price FLOAT DEFAULT 0;
ALTER TABLE crm_quotation_items ADD COLUMN IF NOT EXISTS discount_percent FLOAT DEFAULT 0;
ALTER TABLE crm_quotation_items ADD COLUMN IF NOT EXISTS line_total FLOAT DEFAULT 0;
ALTER TABLE crm_quotation_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.crm_quotations') IS NULL THEN
    RAISE NOTICE 'crm_quotations missing — skip FK fk_crm_quotation_items_quotation_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_quotation_items_quotation_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_quotation_items
    ADD CONSTRAINT fk_crm_quotation_items_quotation_id
    FOREIGN KEY (quotation_id) REFERENCES crm_quotations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_quotation_items_quotation_id: %', SQLERRM;
END $$;

-- ===== crm_quotations =====
CREATE TABLE IF NOT EXISTS crm_quotations (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS quotation_code VARCHAR(50);
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS customer_id VARCHAR(36);
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS opportunity_id VARCHAR(36);
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS price_source VARCHAR(50) DEFAULT 'CATALOG';
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS approval_status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS subtotal FLOAT DEFAULT 0;
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS discount_amount FLOAT DEFAULT 0;
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS total_amount FLOAT DEFAULT 0;
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'VND';
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS valid_until DATE;
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS owner VARCHAR(255);
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE crm_quotations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_crm_quotations_quotation_code ON crm_quotations (quotation_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_crm_quotations_quotation_code'
  ) THEN
    ALTER TABLE crm_quotations
      ADD CONSTRAINT uq_crm_quotations_quotation_code UNIQUE (quotation_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.crm_customers') IS NULL THEN
    RAISE NOTICE 'crm_customers missing — skip FK fk_crm_quotations_customer_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_quotations_customer_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_quotations
    ADD CONSTRAINT fk_crm_quotations_customer_id
    FOREIGN KEY (customer_id) REFERENCES crm_customers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_quotations_customer_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.crm_opportunities') IS NULL THEN
    RAISE NOTICE 'crm_opportunities missing — skip FK fk_crm_quotations_opportunity_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_quotations_opportunity_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_quotations
    ADD CONSTRAINT fk_crm_quotations_opportunity_id
    FOREIGN KEY (opportunity_id) REFERENCES crm_opportunities (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_quotations_opportunity_id: %', SQLERRM;
END $$;

-- ===== crm_sales_contract_prices =====
CREATE TABLE IF NOT EXISTS crm_sales_contract_prices (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_sales_contract_prices ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_sales_contract_prices ADD COLUMN IF NOT EXISTS contract_id VARCHAR(36);
ALTER TABLE crm_sales_contract_prices ADD COLUMN IF NOT EXISTS test_catalog_id VARCHAR(36);
ALTER TABLE crm_sales_contract_prices ADD COLUMN IF NOT EXISTS item_code VARCHAR(50);
ALTER TABLE crm_sales_contract_prices ADD COLUMN IF NOT EXISTS item_name VARCHAR(255);
ALTER TABLE crm_sales_contract_prices ADD COLUMN IF NOT EXISTS standard_price FLOAT DEFAULT 0;
ALTER TABLE crm_sales_contract_prices ADD COLUMN IF NOT EXISTS contract_price FLOAT DEFAULT 0;
ALTER TABLE crm_sales_contract_prices ADD COLUMN IF NOT EXISTS discount_percent FLOAT DEFAULT 0;
ALTER TABLE crm_sales_contract_prices ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.crm_sales_contracts') IS NULL THEN
    RAISE NOTICE 'crm_sales_contracts missing — skip FK fk_crm_sales_contract_prices_contract_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_sales_contract_prices_contract_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_sales_contract_prices
    ADD CONSTRAINT fk_crm_sales_contract_prices_contract_id
    FOREIGN KEY (contract_id) REFERENCES crm_sales_contracts (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_sales_contract_prices_contract_id: %', SQLERRM;
END $$;

-- ===== crm_sales_contracts =====
CREATE TABLE IF NOT EXISTS crm_sales_contracts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS contract_code VARCHAR(50);
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS contract_type VARCHAR(50);
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS customer_id VARCHAR(36);
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS effective_date DATE;
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS expiry_date DATE;
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS renewal_reminder_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS corporate_discount_percent FLOAT DEFAULT 0;
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS owner VARCHAR(255);
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE crm_sales_contracts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_crm_sales_contracts_contract_code ON crm_sales_contracts (contract_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_crm_sales_contracts_contract_code'
  ) THEN
    ALTER TABLE crm_sales_contracts
      ADD CONSTRAINT uq_crm_sales_contracts_contract_code UNIQUE (contract_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.crm_customers') IS NULL THEN
    RAISE NOTICE 'crm_customers missing — skip FK fk_crm_sales_contracts_customer_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_sales_contracts_customer_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_sales_contracts
    ADD CONSTRAINT fk_crm_sales_contracts_customer_id
    FOREIGN KEY (customer_id) REFERENCES crm_customers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_sales_contracts_customer_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.crm_organizations') IS NULL THEN
    RAISE NOTICE 'crm_organizations missing — skip FK fk_crm_sales_contracts_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_crm_sales_contracts_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE crm_sales_contracts
    ADD CONSTRAINT fk_crm_sales_contracts_organization_id
    FOREIGN KEY (organization_id) REFERENCES crm_organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_crm_sales_contracts_organization_id: %', SQLERRM;
END $$;

-- ===== crm_sales_pipelines =====
CREATE TABLE IF NOT EXISTS crm_sales_pipelines (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE crm_sales_pipelines ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE crm_sales_pipelines ADD COLUMN IF NOT EXISTS pipeline_code VARCHAR(50);
ALTER TABLE crm_sales_pipelines ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE crm_sales_pipelines ADD COLUMN IF NOT EXISTS description VARCHAR(500);
ALTER TABLE crm_sales_pipelines ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE;
ALTER TABLE crm_sales_pipelines ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE crm_sales_pipelines ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_crm_sales_pipelines_pipeline_code ON crm_sales_pipelines (pipeline_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_crm_sales_pipelines_pipeline_code'
  ) THEN
    ALTER TABLE crm_sales_pipelines
      ADD CONSTRAINT uq_crm_sales_pipelines_pipeline_code UNIQUE (pipeline_code);
  END IF;
END $$;


-- ===== dashboard_layouts =====
CREATE TABLE IF NOT EXISTS dashboard_layouts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE dashboard_layouts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE dashboard_layouts ADD COLUMN IF NOT EXISTS layout_code VARCHAR(50);
ALTER TABLE dashboard_layouts ADD COLUMN IF NOT EXISTS dashboard_role VARCHAR(50);
ALTER TABLE dashboard_layouts ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE dashboard_layouts ADD COLUMN IF NOT EXISTS widget_ids_json TEXT DEFAULT '[]';
ALTER TABLE dashboard_layouts ADD COLUMN IF NOT EXISTS config_json TEXT DEFAULT '{}';
ALTER TABLE dashboard_layouts ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE;
ALTER TABLE dashboard_layouts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_dashboard_layouts_layout_code ON dashboard_layouts (layout_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_dashboard_layouts_layout_code'
  ) THEN
    ALTER TABLE dashboard_layouts
      ADD CONSTRAINT uq_dashboard_layouts_layout_code UNIQUE (layout_code);
  END IF;
END $$;


-- ===== dashboard_widgets =====
CREATE TABLE IF NOT EXISTS dashboard_widgets (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE dashboard_widgets ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE dashboard_widgets ADD COLUMN IF NOT EXISTS widget_code VARCHAR(50);
ALTER TABLE dashboard_widgets ADD COLUMN IF NOT EXISTS widget_type VARCHAR(50);
ALTER TABLE dashboard_widgets ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE dashboard_widgets ADD COLUMN IF NOT EXISTS dashboard_role VARCHAR(50) DEFAULT 'EXECUTIVE';
ALTER TABLE dashboard_widgets ADD COLUMN IF NOT EXISTS config_json TEXT DEFAULT '{}';
ALTER TABLE dashboard_widgets ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;
ALTER TABLE dashboard_widgets ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE dashboard_widgets ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_dashboard_widgets_widget_code ON dashboard_widgets (widget_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_dashboard_widgets_widget_code'
  ) THEN
    ALTER TABLE dashboard_widgets
      ADD CONSTRAINT uq_dashboard_widgets_widget_code UNIQUE (widget_code);
  END IF;
END $$;


-- ===== diagnostic_categories =====
CREATE TABLE IF NOT EXISTS diagnostic_categories (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE diagnostic_categories ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE diagnostic_categories ADD COLUMN IF NOT EXISTS category_code VARCHAR(50);
ALTER TABLE diagnostic_categories ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE diagnostic_categories ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE diagnostic_categories ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE diagnostic_categories ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE diagnostic_categories ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_diagnostic_categories_category_code ON diagnostic_categories (category_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_diagnostic_categories_category_code'
  ) THEN
    ALTER TABLE diagnostic_categories
      ADD CONSTRAINT uq_diagnostic_categories_category_code UNIQUE (category_code);
  END IF;
END $$;


-- ===== diagnostic_services =====
CREATE TABLE IF NOT EXISTS diagnostic_services (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS service_code VARCHAR(50);
ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS short_name VARCHAR(100);
ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS category_id VARCHAR(36);
ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS sample_type VARCHAR(100);
ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS preparation_instruction TEXT;
ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS fasting_required BOOLEAN DEFAULT FALSE;
ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS estimated_turnaround_hours FLOAT;
ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS home_collection_allowed BOOLEAN DEFAULT FALSE;
ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE diagnostic_services ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_diagnostic_services_service_code ON diagnostic_services (service_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_diagnostic_services_service_code'
  ) THEN
    ALTER TABLE diagnostic_services
      ADD CONSTRAINT uq_diagnostic_services_service_code UNIQUE (service_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.diagnostic_categories') IS NULL THEN
    RAISE NOTICE 'diagnostic_categories missing — skip FK fk_diagnostic_services_category_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_diagnostic_services_category_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE diagnostic_services
    ADD CONSTRAINT fk_diagnostic_services_category_id
    FOREIGN KEY (category_id) REFERENCES diagnostic_categories (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_diagnostic_services_category_id: %', SQLERRM;
END $$;

-- ===== dicom_instance_metadata =====
CREATE TABLE IF NOT EXISTS dicom_instance_metadata (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE dicom_instance_metadata ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE dicom_instance_metadata ADD COLUMN IF NOT EXISTS series_id VARCHAR(36);
ALTER TABLE dicom_instance_metadata ADD COLUMN IF NOT EXISTS sop_instance_uid VARCHAR(255);
ALTER TABLE dicom_instance_metadata ADD COLUMN IF NOT EXISTS instance_number VARCHAR(20);
ALTER TABLE dicom_instance_metadata ADD COLUMN IF NOT EXISTS transfer_syntax VARCHAR(100);
ALTER TABLE dicom_instance_metadata ADD COLUMN IF NOT EXISTS metadata_json TEXT DEFAULT '{}';
ALTER TABLE dicom_instance_metadata ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_dicom_instance_metadata_sop_instance_uid ON dicom_instance_metadata (sop_instance_uid);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_dicom_instance_metadata_sop_instance_uid'
  ) THEN
    ALTER TABLE dicom_instance_metadata
      ADD CONSTRAINT uq_dicom_instance_metadata_sop_instance_uid UNIQUE (sop_instance_uid);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.dicom_series_metadata') IS NULL THEN
    RAISE NOTICE 'dicom_series_metadata missing — skip FK fk_dicom_instance_metadata_series_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_dicom_instance_metadata_series_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE dicom_instance_metadata
    ADD CONSTRAINT fk_dicom_instance_metadata_series_id
    FOREIGN KEY (series_id) REFERENCES dicom_series_metadata (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_dicom_instance_metadata_series_id: %', SQLERRM;
END $$;

-- ===== dicom_series_metadata =====
CREATE TABLE IF NOT EXISTS dicom_series_metadata (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE dicom_series_metadata ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE dicom_series_metadata ADD COLUMN IF NOT EXISTS study_id VARCHAR(36);
ALTER TABLE dicom_series_metadata ADD COLUMN IF NOT EXISTS series_uid VARCHAR(255);
ALTER TABLE dicom_series_metadata ADD COLUMN IF NOT EXISTS series_number VARCHAR(20);
ALTER TABLE dicom_series_metadata ADD COLUMN IF NOT EXISTS modality VARCHAR(20);
ALTER TABLE dicom_series_metadata ADD COLUMN IF NOT EXISTS body_part VARCHAR(100);
ALTER TABLE dicom_series_metadata ADD COLUMN IF NOT EXISTS metadata_json TEXT DEFAULT '{}';
ALTER TABLE dicom_series_metadata ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_dicom_series_metadata_series_uid ON dicom_series_metadata (series_uid);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_dicom_series_metadata_series_uid'
  ) THEN
    ALTER TABLE dicom_series_metadata
      ADD CONSTRAINT uq_dicom_series_metadata_series_uid UNIQUE (series_uid);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.dicom_study_metadata') IS NULL THEN
    RAISE NOTICE 'dicom_study_metadata missing — skip FK fk_dicom_series_metadata_study_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_dicom_series_metadata_study_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE dicom_series_metadata
    ADD CONSTRAINT fk_dicom_series_metadata_study_id
    FOREIGN KEY (study_id) REFERENCES dicom_study_metadata (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_dicom_series_metadata_study_id: %', SQLERRM;
END $$;

-- ===== dicom_study_metadata =====
CREATE TABLE IF NOT EXISTS dicom_study_metadata (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE dicom_study_metadata ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE dicom_study_metadata ADD COLUMN IF NOT EXISTS study_uid VARCHAR(255);
ALTER TABLE dicom_study_metadata ADD COLUMN IF NOT EXISTS patient_id VARCHAR(100);
ALTER TABLE dicom_study_metadata ADD COLUMN IF NOT EXISTS accession_number VARCHAR(100);
ALTER TABLE dicom_study_metadata ADD COLUMN IF NOT EXISTS study_date VARCHAR(20);
ALTER TABLE dicom_study_metadata ADD COLUMN IF NOT EXISTS modality VARCHAR(20);
ALTER TABLE dicom_study_metadata ADD COLUMN IF NOT EXISTS description VARCHAR(500);
ALTER TABLE dicom_study_metadata ADD COLUMN IF NOT EXISTS metadata_json TEXT DEFAULT '{}';
ALTER TABLE dicom_study_metadata ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_dicom_study_metadata_study_uid ON dicom_study_metadata (study_uid);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_dicom_study_metadata_study_uid'
  ) THEN
    ALTER TABLE dicom_study_metadata
      ADD CONSTRAINT uq_dicom_study_metadata_study_uid UNIQUE (study_uid);
  END IF;
END $$;


-- ===== disease_profiles =====
CREATE TABLE IF NOT EXISTS disease_profiles (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE disease_profiles ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE disease_profiles ADD COLUMN IF NOT EXISTS disease_code VARCHAR(50);
ALTER TABLE disease_profiles ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE disease_profiles ADD COLUMN IF NOT EXISTS icd10 VARCHAR(20);
ALTER TABLE disease_profiles ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE disease_profiles ADD COLUMN IF NOT EXISTS test_codes_json TEXT DEFAULT '[]';
ALTER TABLE disease_profiles ADD COLUMN IF NOT EXISTS pattern_json TEXT DEFAULT '{}';
ALTER TABLE disease_profiles ADD COLUMN IF NOT EXISTS evidence_level VARCHAR(10) DEFAULT 'B';
ALTER TABLE disease_profiles ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE disease_profiles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_disease_profiles_disease_code ON disease_profiles (disease_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_disease_profiles_disease_code'
  ) THEN
    ALTER TABLE disease_profiles
      ADD CONSTRAINT uq_disease_profiles_disease_code UNIQUE (disease_code);
  END IF;
END $$;


-- ===== dispatch_items =====
CREATE TABLE IF NOT EXISTS dispatch_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE dispatch_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE dispatch_items ADD COLUMN IF NOT EXISTS dispatch_job_id VARCHAR(36);
ALTER TABLE dispatch_items ADD COLUMN IF NOT EXISTS sample_tracking_id VARCHAR(36);
ALTER TABLE dispatch_items ADD COLUMN IF NOT EXISTS sequence_no INTEGER DEFAULT 1;
ALTER TABLE dispatch_items ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ASSIGNED';
ALTER TABLE dispatch_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== dispatch_jobs =====
CREATE TABLE IF NOT EXISTS dispatch_jobs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS job_code VARCHAR(50);
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS driver_id VARCHAR(36);
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS transport_box_id VARCHAR(36);
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PLANNED';
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS start_latitude VARCHAR(50);
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS start_longitude VARCHAR(50);
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS destination_latitude VARCHAR(50);
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS destination_longitude VARCHAR(50);
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS total_distance_km FLOAT DEFAULT 0;
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS estimated_minutes INTEGER DEFAULT 0;
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS priority VARCHAR(30) DEFAULT 'NORMAL';
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS estimated_arrival VARCHAR(100);
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS actual_arrival VARCHAR(100);
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS delay_minutes INTEGER DEFAULT 0;
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS route_score FLOAT DEFAULT 100;
ALTER TABLE dispatch_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_dispatch_jobs_job_code ON dispatch_jobs (job_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_dispatch_jobs_job_code'
  ) THEN
    ALTER TABLE dispatch_jobs
      ADD CONSTRAINT uq_dispatch_jobs_job_code UNIQUE (job_code);
  END IF;
END $$;


-- ===== doctor_availabilities =====
CREATE TABLE IF NOT EXISTS doctor_availabilities (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE doctor_availabilities ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE doctor_availabilities ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE doctor_availabilities ADD COLUMN IF NOT EXISTS day_of_week VARCHAR(20);
ALTER TABLE doctor_availabilities ADD COLUMN IF NOT EXISTS start_time VARCHAR(10);
ALTER TABLE doctor_availabilities ADD COLUMN IF NOT EXISTS end_time VARCHAR(10);
ALTER TABLE doctor_availabilities ADD COLUMN IF NOT EXISTS location VARCHAR(255);
ALTER TABLE doctor_availabilities ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE doctor_availabilities ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== doctor_commissions =====
CREATE TABLE IF NOT EXISTS doctor_commissions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE doctor_commissions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE doctor_commissions ADD COLUMN IF NOT EXISTS commission_code VARCHAR(50);
ALTER TABLE doctor_commissions ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE doctor_commissions ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE doctor_commissions ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE doctor_commissions ADD COLUMN IF NOT EXISTS amount FLOAT DEFAULT 0;
ALTER TABLE doctor_commissions ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE doctor_commissions ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE doctor_commissions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_doctor_commissions_commission_code ON doctor_commissions (commission_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_doctor_commissions_commission_code'
  ) THEN
    ALTER TABLE doctor_commissions
      ADD CONSTRAINT uq_doctor_commissions_commission_code UNIQUE (commission_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.invoices') IS NULL THEN
    RAISE NOTICE 'invoices missing — skip FK fk_doctor_commissions_invoice_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_doctor_commissions_invoice_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE doctor_commissions
    ADD CONSTRAINT fk_doctor_commissions_invoice_id
    FOREIGN KEY (invoice_id) REFERENCES invoices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_doctor_commissions_invoice_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_doctor_commissions_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_doctor_commissions_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE doctor_commissions
    ADD CONSTRAINT fk_doctor_commissions_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_doctor_commissions_medical_order_id: %', SQLERRM;
END $$;

-- ===== doctor_dashboards =====
CREATE TABLE IF NOT EXISTS doctor_dashboards (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE doctor_dashboards ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE doctor_dashboards ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE doctor_dashboards ADD COLUMN IF NOT EXISTS patients_total INTEGER DEFAULT 0;
ALTER TABLE doctor_dashboards ADD COLUMN IF NOT EXISTS referrals_total INTEGER DEFAULT 0;
ALTER TABLE doctor_dashboards ADD COLUMN IF NOT EXISTS follow_ups_pending INTEGER DEFAULT 0;
ALTER TABLE doctor_dashboards ADD COLUMN IF NOT EXISTS notes_total INTEGER DEFAULT 0;
ALTER TABLE doctor_dashboards ADD COLUMN IF NOT EXISTS released_results_total INTEGER DEFAULT 0;
ALTER TABLE doctor_dashboards ADD COLUMN IF NOT EXISTS schedule_slots INTEGER DEFAULT 0;
ALTER TABLE doctor_dashboards ADD COLUMN IF NOT EXISTS snapshot_json TEXT;
ALTER TABLE doctor_dashboards ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_doctor_dashboards_doctor_id ON doctor_dashboards (doctor_id);



-- ===== doctor_follow_ups =====
CREATE TABLE IF NOT EXISTS doctor_follow_ups (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE doctor_follow_ups ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE doctor_follow_ups ADD COLUMN IF NOT EXISTS follow_up_code VARCHAR(50);
ALTER TABLE doctor_follow_ups ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE doctor_follow_ups ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE doctor_follow_ups ADD COLUMN IF NOT EXISTS follow_up_date TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE doctor_follow_ups ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE doctor_follow_ups ADD COLUMN IF NOT EXISTS reminder_sent BOOLEAN DEFAULT FALSE;
ALTER TABLE doctor_follow_ups ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE doctor_follow_ups ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE doctor_follow_ups ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_doctor_follow_ups_follow_up_code ON doctor_follow_ups (follow_up_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_doctor_follow_ups_follow_up_code'
  ) THEN
    ALTER TABLE doctor_follow_ups
      ADD CONSTRAINT uq_doctor_follow_ups_follow_up_code UNIQUE (follow_up_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_doctor_follow_ups_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_doctor_follow_ups_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE doctor_follow_ups
    ADD CONSTRAINT fk_doctor_follow_ups_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_doctor_follow_ups_patient_id: %', SQLERRM;
END $$;

-- ===== doctor_notes =====
CREATE TABLE IF NOT EXISTS doctor_notes (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS note_text TEXT;
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS note_type VARCHAR(50) DEFAULT 'clinical';
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS visibility VARCHAR(30) DEFAULT 'internal';
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS order_code VARCHAR(50);
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS report_code VARCHAR(50);
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS follow_up_recommendation TEXT;
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE doctor_notes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_doctor_notes_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_doctor_notes_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE doctor_notes
    ADD CONSTRAINT fk_doctor_notes_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_doctor_notes_patient_id: %', SQLERRM;
END $$;

-- ===== doctor_patients =====
CREATE TABLE IF NOT EXISTS doctor_patients (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE doctor_patients ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE doctor_patients ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE doctor_patients ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE doctor_patients ADD COLUMN IF NOT EXISTS relationship_status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE doctor_patients ADD COLUMN IF NOT EXISTS assigned_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE doctor_patients ADD COLUMN IF NOT EXISTS note TEXT;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_doctor_patient'
  ) THEN
    ALTER TABLE doctor_patients
      ADD CONSTRAINT uq_doctor_patient UNIQUE (doctor_id, patient_id);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_doctor_patients_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_doctor_patients_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE doctor_patients
    ADD CONSTRAINT fk_doctor_patients_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_doctor_patients_patient_id: %', SQLERRM;
END $$;

-- ===== doctor_profiles =====
CREATE TABLE IF NOT EXISTS doctor_profiles (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS doctor_code VARCHAR(50);
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS license_number VARCHAR(100);
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS specialty_primary VARCHAR(100);
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS favorite_services_json TEXT DEFAULT '[]';
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS linked_clinics_json TEXT DEFAULT '[]';
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS bio TEXT;
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE doctor_profiles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_doctor_profiles_doctor_id ON doctor_profiles (doctor_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_doctor_profiles_doctor_code ON doctor_profiles (doctor_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_doctor_profiles_doctor_id'
  ) THEN
    ALTER TABLE doctor_profiles
      ADD CONSTRAINT uq_doctor_profiles_doctor_id UNIQUE (doctor_id);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_doctor_profiles_doctor_code'
  ) THEN
    ALTER TABLE doctor_profiles
      ADD CONSTRAINT uq_doctor_profiles_doctor_code UNIQUE (doctor_code);
  END IF;
END $$;


-- ===== doctor_referrals =====
CREATE TABLE IF NOT EXISTS doctor_referrals (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE doctor_referrals ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE doctor_referrals ADD COLUMN IF NOT EXISTS referral_code VARCHAR(50);
ALTER TABLE doctor_referrals ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE doctor_referrals ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE doctor_referrals ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE doctor_referrals ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE doctor_referrals ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE doctor_referrals ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE doctor_referrals ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE doctor_referrals ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE doctor_referrals ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_doctor_referrals_referral_code ON doctor_referrals (referral_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_doctor_referrals_referral_code'
  ) THEN
    ALTER TABLE doctor_referrals
      ADD CONSTRAINT uq_doctor_referrals_referral_code UNIQUE (referral_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_doctor_referrals_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_doctor_referrals_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE doctor_referrals
    ADD CONSTRAINT fk_doctor_referrals_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_doctor_referrals_patient_id: %', SQLERRM;
END $$;

-- ===== doctor_specialties =====
CREATE TABLE IF NOT EXISTS doctor_specialties (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE doctor_specialties ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE doctor_specialties ADD COLUMN IF NOT EXISTS doctor_id VARCHAR(36);
ALTER TABLE doctor_specialties ADD COLUMN IF NOT EXISTS specialty_code VARCHAR(50);
ALTER TABLE doctor_specialties ADD COLUMN IF NOT EXISTS specialty_name VARCHAR(255);
ALTER TABLE doctor_specialties ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT FALSE;
ALTER TABLE doctor_specialties ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== drivers =====
CREATE TABLE IF NOT EXISTS drivers (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE drivers ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS driver_code VARCHAR(50);
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS vehicle_no VARCHAR(50);
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS license_number VARCHAR(100);
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS home_city VARCHAR(100);
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS active_vehicle_id VARCHAR(36);
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS ops_status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE drivers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_drivers_driver_code ON drivers (driver_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_drivers_driver_code'
  ) THEN
    ALTER TABLE drivers
      ADD CONSTRAINT uq_drivers_driver_code UNIQUE (driver_code);
  END IF;
END $$;


-- ===== enterprise_abac_policies =====
CREATE TABLE IF NOT EXISTS enterprise_abac_policies (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_abac_policies ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_abac_policies ADD COLUMN IF NOT EXISTS policy_code VARCHAR(50);
ALTER TABLE enterprise_abac_policies ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE enterprise_abac_policies ADD COLUMN IF NOT EXISTS resource VARCHAR(100);
ALTER TABLE enterprise_abac_policies ADD COLUMN IF NOT EXISTS action VARCHAR(100);
ALTER TABLE enterprise_abac_policies ADD COLUMN IF NOT EXISTS condition_json TEXT DEFAULT '{}';
ALTER TABLE enterprise_abac_policies ADD COLUMN IF NOT EXISTS effect VARCHAR(20) DEFAULT 'ALLOW';
ALTER TABLE enterprise_abac_policies ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE enterprise_abac_policies ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_abac_policies_policy_code ON enterprise_abac_policies (policy_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_abac_policies_policy_code'
  ) THEN
    ALTER TABLE enterprise_abac_policies
      ADD CONSTRAINT uq_enterprise_abac_policies_policy_code UNIQUE (policy_code);
  END IF;
END $$;


-- ===== enterprise_access_history =====
CREATE TABLE IF NOT EXISTS enterprise_access_history (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_access_history ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_access_history ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE enterprise_access_history ADD COLUMN IF NOT EXISTS user_email VARCHAR(255);
ALTER TABLE enterprise_access_history ADD COLUMN IF NOT EXISTS resource VARCHAR(255);
ALTER TABLE enterprise_access_history ADD COLUMN IF NOT EXISTS action VARCHAR(100);
ALTER TABLE enterprise_access_history ADD COLUMN IF NOT EXISTS ip_address VARCHAR(100);
ALTER TABLE enterprise_access_history ADD COLUMN IF NOT EXISTS success BOOLEAN DEFAULT TRUE;
ALTER TABLE enterprise_access_history ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== enterprise_audit_records =====
CREATE TABLE IF NOT EXISTS enterprise_audit_records (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_audit_records ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_audit_records ADD COLUMN IF NOT EXISTS record_hash VARCHAR(64);
ALTER TABLE enterprise_audit_records ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE enterprise_audit_records ADD COLUMN IF NOT EXISTS actor_email VARCHAR(255);
ALTER TABLE enterprise_audit_records ADD COLUMN IF NOT EXISTS action VARCHAR(100);
ALTER TABLE enterprise_audit_records ADD COLUMN IF NOT EXISTS resource_type VARCHAR(100);
ALTER TABLE enterprise_audit_records ADD COLUMN IF NOT EXISTS resource_id VARCHAR(36);
ALTER TABLE enterprise_audit_records ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE enterprise_audit_records ADD COLUMN IF NOT EXISTS previous_hash VARCHAR(64);
ALTER TABLE enterprise_audit_records ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_audit_records_record_hash ON enterprise_audit_records (record_hash);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_audit_records_record_hash'
  ) THEN
    ALTER TABLE enterprise_audit_records
      ADD CONSTRAINT uq_enterprise_audit_records_record_hash UNIQUE (record_hash);
  END IF;
END $$;


-- ===== enterprise_background_jobs =====
CREATE TABLE IF NOT EXISTS enterprise_background_jobs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_background_jobs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_background_jobs ADD COLUMN IF NOT EXISTS job_code VARCHAR(50);
ALTER TABLE enterprise_background_jobs ADD COLUMN IF NOT EXISTS job_type VARCHAR(50);
ALTER TABLE enterprise_background_jobs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE enterprise_background_jobs ADD COLUMN IF NOT EXISTS trace_id VARCHAR(36);
ALTER TABLE enterprise_background_jobs ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE enterprise_background_jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE enterprise_background_jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE enterprise_background_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_background_jobs_job_code ON enterprise_background_jobs (job_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_background_jobs_job_code'
  ) THEN
    ALTER TABLE enterprise_background_jobs
      ADD CONSTRAINT uq_enterprise_background_jobs_job_code UNIQUE (job_code);
  END IF;
END $$;


-- ===== enterprise_business_units =====
CREATE TABLE IF NOT EXISTS enterprise_business_units (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_business_units ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_business_units ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE enterprise_business_units ADD COLUMN IF NOT EXISTS unit_code VARCHAR(50);
ALTER TABLE enterprise_business_units ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE enterprise_business_units ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE enterprise_business_units ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE enterprise_business_units ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_business_units_unit_code ON enterprise_business_units (unit_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_business_units_unit_code'
  ) THEN
    ALTER TABLE enterprise_business_units
      ADD CONSTRAINT uq_enterprise_business_units_unit_code UNIQUE (unit_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.enterprise_tenants') IS NULL THEN
    RAISE NOTICE 'enterprise_tenants missing — skip FK fk_enterprise_business_units_tenant_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_enterprise_business_units_tenant_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE enterprise_business_units
    ADD CONSTRAINT fk_enterprise_business_units_tenant_id
    FOREIGN KEY (tenant_id) REFERENCES enterprise_tenants (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_enterprise_business_units_tenant_id: %', SQLERRM;
END $$;

-- ===== enterprise_compliance_exports =====
CREATE TABLE IF NOT EXISTS enterprise_compliance_exports (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_compliance_exports ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_compliance_exports ADD COLUMN IF NOT EXISTS export_code VARCHAR(50);
ALTER TABLE enterprise_compliance_exports ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE enterprise_compliance_exports ADD COLUMN IF NOT EXISTS export_type VARCHAR(50) DEFAULT 'AUDIT';
ALTER TABLE enterprise_compliance_exports ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'COMPLETED';
ALTER TABLE enterprise_compliance_exports ADD COLUMN IF NOT EXISTS record_count INTEGER DEFAULT 0;
ALTER TABLE enterprise_compliance_exports ADD COLUMN IF NOT EXISTS file_path VARCHAR(500);
ALTER TABLE enterprise_compliance_exports ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_compliance_exports_export_code ON enterprise_compliance_exports (export_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_compliance_exports_export_code'
  ) THEN
    ALTER TABLE enterprise_compliance_exports
      ADD CONSTRAINT uq_enterprise_compliance_exports_export_code UNIQUE (export_code);
  END IF;
END $$;


-- ===== enterprise_departments =====
CREATE TABLE IF NOT EXISTS enterprise_departments (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_departments ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_departments ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE enterprise_departments ADD COLUMN IF NOT EXISTS dept_code VARCHAR(50);
ALTER TABLE enterprise_departments ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE enterprise_departments ADD COLUMN IF NOT EXISTS parent_dept_id VARCHAR(36);
ALTER TABLE enterprise_departments ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 0;
ALTER TABLE enterprise_departments ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE enterprise_departments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_departments_dept_code ON enterprise_departments (dept_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_departments_dept_code'
  ) THEN
    ALTER TABLE enterprise_departments
      ADD CONSTRAINT uq_enterprise_departments_dept_code UNIQUE (dept_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.enterprise_organizations') IS NULL THEN
    RAISE NOTICE 'enterprise_organizations missing — skip FK fk_enterprise_departments_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_enterprise_departments_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE enterprise_departments
    ADD CONSTRAINT fk_enterprise_departments_organization_id
    FOREIGN KEY (organization_id) REFERENCES enterprise_organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_enterprise_departments_organization_id: %', SQLERRM;
END $$;

-- ===== enterprise_feature_flags =====
CREATE TABLE IF NOT EXISTS enterprise_feature_flags (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_feature_flags ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_feature_flags ADD COLUMN IF NOT EXISTS flag_code VARCHAR(50);
ALTER TABLE enterprise_feature_flags ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE enterprise_feature_flags ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT FALSE;
ALTER TABLE enterprise_feature_flags ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE enterprise_feature_flags ADD COLUMN IF NOT EXISTS rollout_percent INTEGER DEFAULT 100;
ALTER TABLE enterprise_feature_flags ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_feature_flags_flag_code ON enterprise_feature_flags (flag_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_feature_flags_flag_code'
  ) THEN
    ALTER TABLE enterprise_feature_flags
      ADD CONSTRAINT uq_enterprise_feature_flags_flag_code UNIQUE (flag_code);
  END IF;
END $$;


-- ===== enterprise_identity_providers =====
CREATE TABLE IF NOT EXISTS enterprise_identity_providers (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_identity_providers ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_identity_providers ADD COLUMN IF NOT EXISTS provider_code VARCHAR(50);
ALTER TABLE enterprise_identity_providers ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE enterprise_identity_providers ADD COLUMN IF NOT EXISTS provider_type VARCHAR(20);
ALTER TABLE enterprise_identity_providers ADD COLUMN IF NOT EXISTS issuer_url VARCHAR(500);
ALTER TABLE enterprise_identity_providers ADD COLUMN IF NOT EXISTS client_id VARCHAR(255);
ALTER TABLE enterprise_identity_providers ADD COLUMN IF NOT EXISTS metadata_json TEXT DEFAULT '{}';
ALTER TABLE enterprise_identity_providers ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE enterprise_identity_providers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_identity_providers_provider_code ON enterprise_identity_providers (provider_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_identity_providers_provider_code'
  ) THEN
    ALTER TABLE enterprise_identity_providers
      ADD CONSTRAINT uq_enterprise_identity_providers_provider_code UNIQUE (provider_code);
  END IF;
END $$;


-- ===== enterprise_licenses =====
CREATE TABLE IF NOT EXISTS enterprise_licenses (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_licenses ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_licenses ADD COLUMN IF NOT EXISTS license_key VARCHAR(100);
ALTER TABLE enterprise_licenses ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE enterprise_licenses ADD COLUMN IF NOT EXISTS plan_code VARCHAR(50);
ALTER TABLE enterprise_licenses ADD COLUMN IF NOT EXISTS seat_limit INTEGER DEFAULT 100;
ALTER TABLE enterprise_licenses ADD COLUMN IF NOT EXISTS feature_flags_json TEXT DEFAULT '[]';
ALTER TABLE enterprise_licenses ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE enterprise_licenses ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE enterprise_licenses ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_licenses_license_key ON enterprise_licenses (license_key);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_licenses_license_key'
  ) THEN
    ALTER TABLE enterprise_licenses
      ADD CONSTRAINT uq_enterprise_licenses_license_key UNIQUE (license_key);
  END IF;
END $$;


-- ===== enterprise_organizations =====
CREATE TABLE IF NOT EXISTS enterprise_organizations (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_organizations ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_organizations ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE enterprise_organizations ADD COLUMN IF NOT EXISTS org_code VARCHAR(50);
ALTER TABLE enterprise_organizations ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE enterprise_organizations ADD COLUMN IF NOT EXISTS parent_org_id VARCHAR(36);
ALTER TABLE enterprise_organizations ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 0;
ALTER TABLE enterprise_organizations ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE enterprise_organizations ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_organizations_org_code ON enterprise_organizations (org_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_organizations_org_code'
  ) THEN
    ALTER TABLE enterprise_organizations
      ADD CONSTRAINT uq_enterprise_organizations_org_code UNIQUE (org_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.enterprise_tenants') IS NULL THEN
    RAISE NOTICE 'enterprise_tenants missing — skip FK fk_enterprise_organizations_tenant_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_enterprise_organizations_tenant_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE enterprise_organizations
    ADD CONSTRAINT fk_enterprise_organizations_tenant_id
    FOREIGN KEY (tenant_id) REFERENCES enterprise_tenants (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_enterprise_organizations_tenant_id: %', SQLERRM;
END $$;

-- ===== enterprise_roles =====
CREATE TABLE IF NOT EXISTS enterprise_roles (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_roles ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_roles ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE enterprise_roles ADD COLUMN IF NOT EXISTS role_code VARCHAR(50);
ALTER TABLE enterprise_roles ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE enterprise_roles ADD COLUMN IF NOT EXISTS permissions_json TEXT DEFAULT '[]';
ALTER TABLE enterprise_roles ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE enterprise_roles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_roles_role_code ON enterprise_roles (role_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_roles_role_code'
  ) THEN
    ALTER TABLE enterprise_roles
      ADD CONSTRAINT uq_enterprise_roles_role_code UNIQUE (role_code);
  END IF;
END $$;


-- ===== enterprise_security_events =====
CREATE TABLE IF NOT EXISTS enterprise_security_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_security_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_security_events ADD COLUMN IF NOT EXISTS event_code VARCHAR(50);
ALTER TABLE enterprise_security_events ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE enterprise_security_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(50);
ALTER TABLE enterprise_security_events ADD COLUMN IF NOT EXISTS severity VARCHAR(20) DEFAULT 'INFO';
ALTER TABLE enterprise_security_events ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE enterprise_security_events ADD COLUMN IF NOT EXISTS metadata_json TEXT DEFAULT '{}';
ALTER TABLE enterprise_security_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_security_events_event_code ON enterprise_security_events (event_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_security_events_event_code'
  ) THEN
    ALTER TABLE enterprise_security_events
      ADD CONSTRAINT uq_enterprise_security_events_event_code UNIQUE (event_code);
  END IF;
END $$;


-- ===== enterprise_system_settings =====
CREATE TABLE IF NOT EXISTS enterprise_system_settings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_system_settings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_system_settings ADD COLUMN IF NOT EXISTS setting_key VARCHAR(100);
ALTER TABLE enterprise_system_settings ADD COLUMN IF NOT EXISTS setting_value TEXT;
ALTER TABLE enterprise_system_settings ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'GENERAL';
ALTER TABLE enterprise_system_settings ADD COLUMN IF NOT EXISTS is_secret BOOLEAN DEFAULT FALSE;
ALTER TABLE enterprise_system_settings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_system_settings_setting_key ON enterprise_system_settings (setting_key);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_system_settings_setting_key'
  ) THEN
    ALTER TABLE enterprise_system_settings
      ADD CONSTRAINT uq_enterprise_system_settings_setting_key UNIQUE (setting_key);
  END IF;
END $$;


-- ===== enterprise_tenants =====
CREATE TABLE IF NOT EXISTS enterprise_tenants (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_tenants ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_tenants ADD COLUMN IF NOT EXISTS tenant_code VARCHAR(50);
ALTER TABLE enterprise_tenants ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE enterprise_tenants ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE enterprise_tenants ADD COLUMN IF NOT EXISTS isolation_mode VARCHAR(50) DEFAULT 'STRICT';
ALTER TABLE enterprise_tenants ADD COLUMN IF NOT EXISTS schema_name VARCHAR(100);
ALTER TABLE enterprise_tenants ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_enterprise_tenants_tenant_code ON enterprise_tenants (tenant_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_enterprise_tenants_tenant_code'
  ) THEN
    ALTER TABLE enterprise_tenants
      ADD CONSTRAINT uq_enterprise_tenants_tenant_code UNIQUE (tenant_code);
  END IF;
END $$;


-- ===== enterprise_usage_metrics =====
CREATE TABLE IF NOT EXISTS enterprise_usage_metrics (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE enterprise_usage_metrics ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE enterprise_usage_metrics ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE enterprise_usage_metrics ADD COLUMN IF NOT EXISTS metric_code VARCHAR(50);
ALTER TABLE enterprise_usage_metrics ADD COLUMN IF NOT EXISTS metric_value FLOAT DEFAULT 0;
ALTER TABLE enterprise_usage_metrics ADD COLUMN IF NOT EXISTS period VARCHAR(20) DEFAULT 'DAILY';
ALTER TABLE enterprise_usage_metrics ADD COLUMN IF NOT EXISTS recorded_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== event_dedup_records =====
CREATE TABLE IF NOT EXISTS event_dedup_records (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE event_dedup_records ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE event_dedup_records ADD COLUMN IF NOT EXISTS fingerprint VARCHAR(128);
ALTER TABLE event_dedup_records ADD COLUMN IF NOT EXISTS event_id VARCHAR(36);
ALTER TABLE event_dedup_records ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_event_dedup_records_fingerprint ON event_dedup_records (fingerprint);



-- ===== event_logs =====
CREATE TABLE IF NOT EXISTS event_logs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE event_logs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE event_logs ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE event_logs ADD COLUMN IF NOT EXISTS object_type VARCHAR(100);
ALTER TABLE event_logs ADD COLUMN IF NOT EXISTS object_id VARCHAR(100);
ALTER TABLE event_logs ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE event_logs ADD COLUMN IF NOT EXISTS severity VARCHAR(50) DEFAULT 'INFO';
ALTER TABLE event_logs ADD COLUMN IF NOT EXISTS request_id VARCHAR(36);
ALTER TABLE event_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== federated_labs =====
CREATE TABLE IF NOT EXISTS federated_labs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS lab_code VARCHAR(50);
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS city VARCHAR(100);
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS latitude FLOAT;
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS longitude FLOAT;
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'OFFLINE';
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS connection_status VARCHAR(50) DEFAULT 'DISCONNECTED';
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 50;
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS sla_minutes INTEGER DEFAULT 240;
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS contract_active BOOLEAN DEFAULT TRUE;
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS base_price FLOAT DEFAULT 0;
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS metadata_json TEXT DEFAULT '{}';
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS connected_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE federated_labs ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federated_labs_lab_code ON federated_labs (lab_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federated_labs_lab_code'
  ) THEN
    ALTER TABLE federated_labs
      ADD CONSTRAINT uq_federated_labs_lab_code UNIQUE (lab_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.federation_providers') IS NULL THEN
    RAISE NOTICE 'federation_providers missing — skip FK fk_federated_labs_provider_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federated_labs_provider_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federated_labs
    ADD CONSTRAINT fk_federated_labs_provider_id
    FOREIGN KEY (provider_id) REFERENCES federation_providers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federated_labs_provider_id: %', SQLERRM;
END $$;

-- ===== federation_analyzer_capacities =====
CREATE TABLE IF NOT EXISTS federation_analyzer_capacities (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_analyzer_capacities ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_analyzer_capacities ADD COLUMN IF NOT EXISTS analyzer_code VARCHAR(50);
ALTER TABLE federation_analyzer_capacities ADD COLUMN IF NOT EXISTS federated_lab_id VARCHAR(36);
ALTER TABLE federation_analyzer_capacities ADD COLUMN IF NOT EXISTS analyzer_name VARCHAR(255);
ALTER TABLE federation_analyzer_capacities ADD COLUMN IF NOT EXISTS hourly_throughput INTEGER DEFAULT 20;
ALTER TABLE federation_analyzer_capacities ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ONLINE';
ALTER TABLE federation_analyzer_capacities ADD COLUMN IF NOT EXISTS qc_status VARCHAR(50) DEFAULT 'PASS';
ALTER TABLE federation_analyzer_capacities ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.federated_labs') IS NULL THEN
    RAISE NOTICE 'federated_labs missing — skip FK fk_federation_analyzer_capacities_federated_lab_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_analyzer_capacities_federated_lab_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_analyzer_capacities
    ADD CONSTRAINT fk_federation_analyzer_capacities_federated_lab_id
    FOREIGN KEY (federated_lab_id) REFERENCES federated_labs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_analyzer_capacities_federated_lab_id: %', SQLERRM;
END $$;

-- ===== federation_capabilities =====
CREATE TABLE IF NOT EXISTS federation_capabilities (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_capabilities ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_capabilities ADD COLUMN IF NOT EXISTS capability_code VARCHAR(50);
ALTER TABLE federation_capabilities ADD COLUMN IF NOT EXISTS federated_lab_id VARCHAR(36);
ALTER TABLE federation_capabilities ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE federation_capabilities ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE federation_capabilities ADD COLUMN IF NOT EXISTS modality VARCHAR(50) DEFAULT 'LAB';
ALTER TABLE federation_capabilities ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE federation_capabilities ADD COLUMN IF NOT EXISTS turnaround_hours INTEGER DEFAULT 24;
ALTER TABLE federation_capabilities ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.federated_labs') IS NULL THEN
    RAISE NOTICE 'federated_labs missing — skip FK fk_federation_capabilities_federated_lab_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_capabilities_federated_lab_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_capabilities
    ADD CONSTRAINT fk_federation_capabilities_federated_lab_id
    FOREIGN KEY (federated_lab_id) REFERENCES federated_labs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_capabilities_federated_lab_id: %', SQLERRM;
END $$;

-- ===== federation_capacity_rules =====
CREATE TABLE IF NOT EXISTS federation_capacity_rules (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_capacity_rules ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_capacity_rules ADD COLUMN IF NOT EXISTS rule_code VARCHAR(50);
ALTER TABLE federation_capacity_rules ADD COLUMN IF NOT EXISTS federated_lab_id VARCHAR(36);
ALTER TABLE federation_capacity_rules ADD COLUMN IF NOT EXISTS max_daily_tests INTEGER DEFAULT 500;
ALTER TABLE federation_capacity_rules ADD COLUMN IF NOT EXISTS warning_threshold FLOAT DEFAULT 0.8;
ALTER TABLE federation_capacity_rules ADD COLUMN IF NOT EXISTS block_threshold FLOAT DEFAULT 0.95;
ALTER TABLE federation_capacity_rules ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE federation_capacity_rules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federation_capacity_rules_rule_code ON federation_capacity_rules (rule_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federation_capacity_rules_rule_code'
  ) THEN
    ALTER TABLE federation_capacity_rules
      ADD CONSTRAINT uq_federation_capacity_rules_rule_code UNIQUE (rule_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.federated_labs') IS NULL THEN
    RAISE NOTICE 'federated_labs missing — skip FK fk_federation_capacity_rules_federated_lab_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_capacity_rules_federated_lab_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_capacity_rules
    ADD CONSTRAINT fk_federation_capacity_rules_federated_lab_id
    FOREIGN KEY (federated_lab_id) REFERENCES federated_labs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_capacity_rules_federated_lab_id: %', SQLERRM;
END $$;

-- ===== federation_capacity_snapshots =====
CREATE TABLE IF NOT EXISTS federation_capacity_snapshots (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_capacity_snapshots ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_capacity_snapshots ADD COLUMN IF NOT EXISTS snapshot_code VARCHAR(50);
ALTER TABLE federation_capacity_snapshots ADD COLUMN IF NOT EXISTS federated_lab_id VARCHAR(36);
ALTER TABLE federation_capacity_snapshots ADD COLUMN IF NOT EXISTS snapshot_date TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE federation_capacity_snapshots ADD COLUMN IF NOT EXISTS total_capacity INTEGER DEFAULT 0;
ALTER TABLE federation_capacity_snapshots ADD COLUMN IF NOT EXISTS used_capacity INTEGER DEFAULT 0;
ALTER TABLE federation_capacity_snapshots ADD COLUMN IF NOT EXISTS remaining_capacity INTEGER DEFAULT 0;
ALTER TABLE federation_capacity_snapshots ADD COLUMN IF NOT EXISTS utilization_rate FLOAT DEFAULT 0;
ALTER TABLE federation_capacity_snapshots ADD COLUMN IF NOT EXISTS metrics_json TEXT DEFAULT '{}';
ALTER TABLE federation_capacity_snapshots ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federation_capacity_snapshots_snapshot_code ON federation_capacity_snapshots (snapshot_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federation_capacity_snapshots_snapshot_code'
  ) THEN
    ALTER TABLE federation_capacity_snapshots
      ADD CONSTRAINT uq_federation_capacity_snapshots_snapshot_code UNIQUE (snapshot_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.federated_labs') IS NULL THEN
    RAISE NOTICE 'federated_labs missing — skip FK fk_federation_capacity_snapshots_federated_lab_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_capacity_snapshots_federated_lab_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_capacity_snapshots
    ADD CONSTRAINT fk_federation_capacity_snapshots_federated_lab_id
    FOREIGN KEY (federated_lab_id) REFERENCES federated_labs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_capacity_snapshots_federated_lab_id: %', SQLERRM;
END $$;

-- ===== federation_events =====
CREATE TABLE IF NOT EXISTS federation_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_events ADD COLUMN IF NOT EXISTS event_code VARCHAR(50);
ALTER TABLE federation_events ADD COLUMN IF NOT EXISTS federated_lab_id VARCHAR(36);
ALTER TABLE federation_events ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE federation_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(50);
ALTER TABLE federation_events ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE federation_events ADD COLUMN IF NOT EXISTS severity VARCHAR(20) DEFAULT 'INFO';
ALTER TABLE federation_events ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE federation_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federation_events_event_code ON federation_events (event_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federation_events_event_code'
  ) THEN
    ALTER TABLE federation_events
      ADD CONSTRAINT uq_federation_events_event_code UNIQUE (event_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.federation_providers') IS NULL THEN
    RAISE NOTICE 'federation_providers missing — skip FK fk_federation_events_provider_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_events_provider_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_events
    ADD CONSTRAINT fk_federation_events_provider_id
    FOREIGN KEY (provider_id) REFERENCES federation_providers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_events_provider_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.federated_labs') IS NULL THEN
    RAISE NOTICE 'federated_labs missing — skip FK fk_federation_events_federated_lab_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_events_federated_lab_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_events
    ADD CONSTRAINT fk_federation_events_federated_lab_id
    FOREIGN KEY (federated_lab_id) REFERENCES federated_labs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_events_federated_lab_id: %', SQLERRM;
END $$;

-- ===== federation_failover_events =====
CREATE TABLE IF NOT EXISTS federation_failover_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_failover_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_failover_events ADD COLUMN IF NOT EXISTS event_code VARCHAR(50);
ALTER TABLE federation_failover_events ADD COLUMN IF NOT EXISTS trigger_type VARCHAR(50);
ALTER TABLE federation_failover_events ADD COLUMN IF NOT EXISTS source_lab_id VARCHAR(36);
ALTER TABLE federation_failover_events ADD COLUMN IF NOT EXISTS fallback_lab_id VARCHAR(36);
ALTER TABLE federation_failover_events ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'TRIGGERED';
ALTER TABLE federation_failover_events ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE federation_failover_events ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE federation_failover_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federation_failover_events_event_code ON federation_failover_events (event_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federation_failover_events_event_code'
  ) THEN
    ALTER TABLE federation_failover_events
      ADD CONSTRAINT uq_federation_failover_events_event_code UNIQUE (event_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.federated_labs') IS NULL THEN
    RAISE NOTICE 'federated_labs missing — skip FK fk_federation_failover_events_source_lab_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_failover_events_source_lab_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_failover_events
    ADD CONSTRAINT fk_federation_failover_events_source_lab_id
    FOREIGN KEY (source_lab_id) REFERENCES federated_labs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_failover_events_source_lab_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.federated_labs') IS NULL THEN
    RAISE NOTICE 'federated_labs missing — skip FK fk_federation_failover_events_fallback_lab_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_failover_events_fallback_lab_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_failover_events
    ADD CONSTRAINT fk_federation_failover_events_fallback_lab_id
    FOREIGN KEY (fallback_lab_id) REFERENCES federated_labs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_failover_events_fallback_lab_id: %', SQLERRM;
END $$;

-- ===== federation_failover_rules =====
CREATE TABLE IF NOT EXISTS federation_failover_rules (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_failover_rules ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_failover_rules ADD COLUMN IF NOT EXISTS rule_code VARCHAR(50);
ALTER TABLE federation_failover_rules ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE federation_failover_rules ADD COLUMN IF NOT EXISTS trigger_type VARCHAR(50);
ALTER TABLE federation_failover_rules ADD COLUMN IF NOT EXISTS target_lab_id VARCHAR(36);
ALTER TABLE federation_failover_rules ADD COLUMN IF NOT EXISTS fallback_lab_id VARCHAR(36);
ALTER TABLE federation_failover_rules ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE federation_failover_rules ADD COLUMN IF NOT EXISTS config_json TEXT DEFAULT '{}';
ALTER TABLE federation_failover_rules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federation_failover_rules_rule_code ON federation_failover_rules (rule_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federation_failover_rules_rule_code'
  ) THEN
    ALTER TABLE federation_failover_rules
      ADD CONSTRAINT uq_federation_failover_rules_rule_code UNIQUE (rule_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.federated_labs') IS NULL THEN
    RAISE NOTICE 'federated_labs missing — skip FK fk_federation_failover_rules_target_lab_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_failover_rules_target_lab_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_failover_rules
    ADD CONSTRAINT fk_federation_failover_rules_target_lab_id
    FOREIGN KEY (target_lab_id) REFERENCES federated_labs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_failover_rules_target_lab_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.federated_labs') IS NULL THEN
    RAISE NOTICE 'federated_labs missing — skip FK fk_federation_failover_rules_fallback_lab_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_failover_rules_fallback_lab_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_failover_rules
    ADD CONSTRAINT fk_federation_failover_rules_fallback_lab_id
    FOREIGN KEY (fallback_lab_id) REFERENCES federated_labs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_failover_rules_fallback_lab_id: %', SQLERRM;
END $$;

-- ===== federation_lab_workload_snapshots =====
CREATE TABLE IF NOT EXISTS federation_lab_workload_snapshots (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_lab_workload_snapshots ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_lab_workload_snapshots ADD COLUMN IF NOT EXISTS snapshot_code VARCHAR(50);
ALTER TABLE federation_lab_workload_snapshots ADD COLUMN IF NOT EXISTS federated_lab_id VARCHAR(36);
ALTER TABLE federation_lab_workload_snapshots ADD COLUMN IF NOT EXISTS snapshot_date TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE federation_lab_workload_snapshots ADD COLUMN IF NOT EXISTS pending_orders INTEGER DEFAULT 0;
ALTER TABLE federation_lab_workload_snapshots ADD COLUMN IF NOT EXISTS in_progress_tests INTEGER DEFAULT 0;
ALTER TABLE federation_lab_workload_snapshots ADD COLUMN IF NOT EXISTS completed_tests INTEGER DEFAULT 0;
ALTER TABLE federation_lab_workload_snapshots ADD COLUMN IF NOT EXISTS average_tat_hours FLOAT DEFAULT 0;
ALTER TABLE federation_lab_workload_snapshots ADD COLUMN IF NOT EXISTS qc_issue_rate FLOAT DEFAULT 0;
ALTER TABLE federation_lab_workload_snapshots ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federation_lab_workload_snapshots_snapshot_code ON federation_lab_workload_snapshots (snapshot_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federation_lab_workload_snapshots_snapshot_code'
  ) THEN
    ALTER TABLE federation_lab_workload_snapshots
      ADD CONSTRAINT uq_federation_lab_workload_snapshots_snapshot_code UNIQUE (snapshot_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.federated_labs') IS NULL THEN
    RAISE NOTICE 'federated_labs missing — skip FK fk_federation_lab_workload_snapshots_federated_lab_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_lab_workload_snapshots_federated_lab_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_lab_workload_snapshots
    ADD CONSTRAINT fk_federation_lab_workload_snapshots_federated_lab_id
    FOREIGN KEY (federated_lab_id) REFERENCES federated_labs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_lab_workload_snapshots_federated_lab_id: %', SQLERRM;
END $$;

-- ===== federation_policies =====
CREATE TABLE IF NOT EXISTS federation_policies (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_policies ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_policies ADD COLUMN IF NOT EXISTS policy_code VARCHAR(50);
ALTER TABLE federation_policies ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE federation_policies ADD COLUMN IF NOT EXISTS policy_type VARCHAR(50) DEFAULT 'ROUTING';
ALTER TABLE federation_policies ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE federation_policies ADD COLUMN IF NOT EXISTS rules_json TEXT DEFAULT '{}';
ALTER TABLE federation_policies ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE federation_policies ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federation_policies_policy_code ON federation_policies (policy_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federation_policies_policy_code'
  ) THEN
    ALTER TABLE federation_policies
      ADD CONSTRAINT uq_federation_policies_policy_code UNIQUE (policy_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.federation_providers') IS NULL THEN
    RAISE NOTICE 'federation_providers missing — skip FK fk_federation_policies_provider_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_policies_provider_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_policies
    ADD CONSTRAINT fk_federation_policies_provider_id
    FOREIGN KEY (provider_id) REFERENCES federation_providers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_policies_provider_id: %', SQLERRM;
END $$;

-- ===== federation_provider_branches =====
CREATE TABLE IF NOT EXISTS federation_provider_branches (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_provider_branches ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_provider_branches ADD COLUMN IF NOT EXISTS branch_code VARCHAR(50);
ALTER TABLE federation_provider_branches ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE federation_provider_branches ADD COLUMN IF NOT EXISTS federated_lab_id VARCHAR(36);
ALTER TABLE federation_provider_branches ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE federation_provider_branches ADD COLUMN IF NOT EXISTS city VARCHAR(100);
ALTER TABLE federation_provider_branches ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE federation_provider_branches ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE federation_provider_branches ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federation_provider_branches_branch_code ON federation_provider_branches (branch_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federation_provider_branches_branch_code'
  ) THEN
    ALTER TABLE federation_provider_branches
      ADD CONSTRAINT uq_federation_provider_branches_branch_code UNIQUE (branch_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.federated_labs') IS NULL THEN
    RAISE NOTICE 'federated_labs missing — skip FK fk_federation_provider_branches_federated_lab_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_provider_branches_federated_lab_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_provider_branches
    ADD CONSTRAINT fk_federation_provider_branches_federated_lab_id
    FOREIGN KEY (federated_lab_id) REFERENCES federated_labs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_provider_branches_federated_lab_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.federation_providers') IS NULL THEN
    RAISE NOTICE 'federation_providers missing — skip FK fk_federation_provider_branches_provider_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_provider_branches_provider_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_provider_branches
    ADD CONSTRAINT fk_federation_provider_branches_provider_id
    FOREIGN KEY (provider_id) REFERENCES federation_providers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_provider_branches_provider_id: %', SQLERRM;
END $$;

-- ===== federation_providers =====
CREATE TABLE IF NOT EXISTS federation_providers (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_providers ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_providers ADD COLUMN IF NOT EXISTS provider_code VARCHAR(50);
ALTER TABLE federation_providers ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE federation_providers ADD COLUMN IF NOT EXISTS provider_type VARCHAR(50) DEFAULT 'LAB_NETWORK';
ALTER TABLE federation_providers ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255);
ALTER TABLE federation_providers ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(30);
ALTER TABLE federation_providers ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE federation_providers ADD COLUMN IF NOT EXISTS settings_json TEXT DEFAULT '{}';
ALTER TABLE federation_providers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federation_providers_provider_code ON federation_providers (provider_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federation_providers_provider_code'
  ) THEN
    ALTER TABLE federation_providers
      ADD CONSTRAINT uq_federation_providers_provider_code UNIQUE (provider_code);
  END IF;
END $$;


-- ===== federation_routing_audits =====
CREATE TABLE IF NOT EXISTS federation_routing_audits (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_routing_audits ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_routing_audits ADD COLUMN IF NOT EXISTS audit_code VARCHAR(50);
ALTER TABLE federation_routing_audits ADD COLUMN IF NOT EXISTS routing_decision_id VARCHAR(36);
ALTER TABLE federation_routing_audits ADD COLUMN IF NOT EXISTS action VARCHAR(50);
ALTER TABLE federation_routing_audits ADD COLUMN IF NOT EXISTS actor_email VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE federation_routing_audits ADD COLUMN IF NOT EXISTS details_json TEXT;
ALTER TABLE federation_routing_audits ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federation_routing_audits_audit_code ON federation_routing_audits (audit_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federation_routing_audits_audit_code'
  ) THEN
    ALTER TABLE federation_routing_audits
      ADD CONSTRAINT uq_federation_routing_audits_audit_code UNIQUE (audit_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.federation_routing_decisions') IS NULL THEN
    RAISE NOTICE 'federation_routing_decisions missing — skip FK fk_federation_routing_audits_routing_decision_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_routing_audits_routing_decision_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_routing_audits
    ADD CONSTRAINT fk_federation_routing_audits_routing_decision_id
    FOREIGN KEY (routing_decision_id) REFERENCES federation_routing_decisions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_routing_audits_routing_decision_id: %', SQLERRM;
END $$;

-- ===== federation_routing_decisions =====
CREATE TABLE IF NOT EXISTS federation_routing_decisions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_routing_decisions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_routing_decisions ADD COLUMN IF NOT EXISTS decision_code VARCHAR(50);
ALTER TABLE federation_routing_decisions ADD COLUMN IF NOT EXISTS request_ref VARCHAR(100);
ALTER TABLE federation_routing_decisions ADD COLUMN IF NOT EXISTS selected_lab_id VARCHAR(36);
ALTER TABLE federation_routing_decisions ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE federation_routing_decisions ADD COLUMN IF NOT EXISTS score_total FLOAT DEFAULT 0;
ALTER TABLE federation_routing_decisions ADD COLUMN IF NOT EXISTS score_breakdown_json TEXT;
ALTER TABLE federation_routing_decisions ADD COLUMN IF NOT EXISTS candidate_count INTEGER DEFAULT 0;
ALTER TABLE federation_routing_decisions ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'SELECTED';
ALTER TABLE federation_routing_decisions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federation_routing_decisions_decision_code ON federation_routing_decisions (decision_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federation_routing_decisions_decision_code'
  ) THEN
    ALTER TABLE federation_routing_decisions
      ADD CONSTRAINT uq_federation_routing_decisions_decision_code UNIQUE (decision_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.federated_labs') IS NULL THEN
    RAISE NOTICE 'federated_labs missing — skip FK fk_federation_routing_decisions_selected_lab_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_federation_routing_decisions_selected_lab_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE federation_routing_decisions
    ADD CONSTRAINT fk_federation_routing_decisions_selected_lab_id
    FOREIGN KEY (selected_lab_id) REFERENCES federated_labs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_federation_routing_decisions_selected_lab_id: %', SQLERRM;
END $$;

-- ===== federation_routing_rules =====
CREATE TABLE IF NOT EXISTS federation_routing_rules (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS rule_code VARCHAR(50);
ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS weight_distance FLOAT DEFAULT 0.15;
ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS weight_capacity FLOAT DEFAULT 0.15;
ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS weight_sla FLOAT DEFAULT 0.15;
ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS weight_contract FLOAT DEFAULT 0.1;
ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS weight_price FLOAT DEFAULT 0.1;
ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS weight_capability FLOAT DEFAULT 0.15;
ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS weight_priority FLOAT DEFAULT 0.1;
ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS weight_online FLOAT DEFAULT 0.1;
ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE federation_routing_rules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_federation_routing_rules_rule_code ON federation_routing_rules (rule_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_federation_routing_rules_rule_code'
  ) THEN
    ALTER TABLE federation_routing_rules
      ADD CONSTRAINT uq_federation_routing_rules_rule_code UNIQUE (rule_code);
  END IF;
END $$;


-- ===== file_metadata =====
CREATE TABLE IF NOT EXISTS file_metadata (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(64);
ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS filename VARCHAR(255);
ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS content_type VARCHAR(128) DEFAULT 'application/octet-stream';
ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS size_bytes INTEGER DEFAULT 0;
ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS storage_provider VARCHAR(32) DEFAULT 'local';
ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS storage_key VARCHAR(512);
ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS checksum_sha256 VARCHAR(64);
ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS status VARCHAR(32) DEFAULT 'ACTIVE';
ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS virus_scan_status VARCHAR(32) DEFAULT 'PENDING';
ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS retention_until VARCHAR(32);
ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS created_at VARCHAR(32);
ALTER TABLE file_metadata ADD COLUMN IF NOT EXISTS updated_at VARCHAR(32);




-- ===== gps_readings =====
CREATE TABLE IF NOT EXISTS gps_readings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE gps_readings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE gps_readings ADD COLUMN IF NOT EXISTS device_id VARCHAR(36);
ALTER TABLE gps_readings ADD COLUMN IF NOT EXISTS latitude FLOAT;
ALTER TABLE gps_readings ADD COLUMN IF NOT EXISTS longitude FLOAT;
ALTER TABLE gps_readings ADD COLUMN IF NOT EXISTS recorded_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.iot_devices') IS NULL THEN
    RAISE NOTICE 'iot_devices missing — skip FK fk_gps_readings_device_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_gps_readings_device_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE gps_readings
    ADD CONSTRAINT fk_gps_readings_device_id
    FOREIGN KEY (device_id) REFERENCES iot_devices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_gps_readings_device_id: %', SQLERRM;
END $$;

-- ===== his_patient_messages =====
CREATE TABLE IF NOT EXISTS his_patient_messages (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE his_patient_messages ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE his_patient_messages ADD COLUMN IF NOT EXISTS message_id VARCHAR(36);
ALTER TABLE his_patient_messages ADD COLUMN IF NOT EXISTS external_patient_id VARCHAR(100);
ALTER TABLE his_patient_messages ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE his_patient_messages ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
ALTER TABLE his_patient_messages ADD COLUMN IF NOT EXISTS date_of_birth VARCHAR(20);
ALTER TABLE his_patient_messages ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE his_patient_messages ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.integration_messages') IS NULL THEN
    RAISE NOTICE 'integration_messages missing — skip FK fk_his_patient_messages_message_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_his_patient_messages_message_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE his_patient_messages
    ADD CONSTRAINT fk_his_patient_messages_message_id
    FOREIGN KEY (message_id) REFERENCES integration_messages (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_his_patient_messages_message_id: %', SQLERRM;
END $$;

-- ===== home_collections =====
CREATE TABLE IF NOT EXISTS home_collections (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE home_collections ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE home_collections ADD COLUMN IF NOT EXISTS patient_id VARCHAR(36);
ALTER TABLE home_collections ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE home_collections ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE home_collections ADD COLUMN IF NOT EXISTS scheduled_time VARCHAR(100);
ALTER TABLE home_collections ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'REQUESTED';
ALTER TABLE home_collections ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== home_sampling_requests =====
CREATE TABLE IF NOT EXISTS home_sampling_requests (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE home_sampling_requests ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE home_sampling_requests ADD COLUMN IF NOT EXISTS patient_id VARCHAR(36);
ALTER TABLE home_sampling_requests ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE home_sampling_requests ADD COLUMN IF NOT EXISTS preferred_time VARCHAR(255);
ALTER TABLE home_sampling_requests ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE home_sampling_requests ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== humidity_readings =====
CREATE TABLE IF NOT EXISTS humidity_readings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE humidity_readings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE humidity_readings ADD COLUMN IF NOT EXISTS device_id VARCHAR(36);
ALTER TABLE humidity_readings ADD COLUMN IF NOT EXISTS humidity_percent FLOAT;
ALTER TABLE humidity_readings ADD COLUMN IF NOT EXISTS recorded_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.iot_devices') IS NULL THEN
    RAISE NOTICE 'iot_devices missing — skip FK fk_humidity_readings_device_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_humidity_readings_device_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE humidity_readings
    ADD CONSTRAINT fk_humidity_readings_device_id
    FOREIGN KEY (device_id) REFERENCES iot_devices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_humidity_readings_device_id: %', SQLERRM;
END $$;

-- ===== incidents =====
CREATE TABLE IF NOT EXISTS incidents (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE incidents ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS incident_code VARCHAR(50);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS incident_type VARCHAR(100);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS severity VARCHAR(30) DEFAULT 'MEDIUM';
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS related_object_type VARCHAR(100);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS related_object_id VARCHAR(100);
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'OPEN';
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE incidents ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_incidents_incident_code ON incidents (incident_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_incidents_incident_code'
  ) THEN
    ALTER TABLE incidents
      ADD CONSTRAINT uq_incidents_incident_code UNIQUE (incident_code);
  END IF;
END $$;


-- ===== infra_recovery_artifacts =====
CREATE TABLE IF NOT EXISTS infra_recovery_artifacts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE infra_recovery_artifacts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE infra_recovery_artifacts ADD COLUMN IF NOT EXISTS plan_id VARCHAR(36);
ALTER TABLE infra_recovery_artifacts ADD COLUMN IF NOT EXISTS artifact_code VARCHAR(50);
ALTER TABLE infra_recovery_artifacts ADD COLUMN IF NOT EXISTS artifact_type VARCHAR(50);
ALTER TABLE infra_recovery_artifacts ADD COLUMN IF NOT EXISTS checksum VARCHAR(128);
ALTER TABLE infra_recovery_artifacts ADD COLUMN IF NOT EXISTS storage_path VARCHAR(500);
ALTER TABLE infra_recovery_artifacts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_infra_recovery_artifacts_artifact_code ON infra_recovery_artifacts (artifact_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_infra_recovery_artifacts_artifact_code'
  ) THEN
    ALTER TABLE infra_recovery_artifacts
      ADD CONSTRAINT uq_infra_recovery_artifacts_artifact_code UNIQUE (artifact_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.infra_recovery_plans') IS NULL THEN
    RAISE NOTICE 'infra_recovery_plans missing — skip FK fk_infra_recovery_artifacts_plan_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_infra_recovery_artifacts_plan_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE infra_recovery_artifacts
    ADD CONSTRAINT fk_infra_recovery_artifacts_plan_id
    FOREIGN KEY (plan_id) REFERENCES infra_recovery_plans (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_infra_recovery_artifacts_plan_id: %', SQLERRM;
END $$;

-- ===== infra_recovery_plans =====
CREATE TABLE IF NOT EXISTS infra_recovery_plans (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE infra_recovery_plans ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE infra_recovery_plans ADD COLUMN IF NOT EXISTS plan_code VARCHAR(50);
ALTER TABLE infra_recovery_plans ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE infra_recovery_plans ADD COLUMN IF NOT EXISTS rto_minutes INTEGER DEFAULT 60;
ALTER TABLE infra_recovery_plans ADD COLUMN IF NOT EXISTS rpo_minutes INTEGER DEFAULT 15;
ALTER TABLE infra_recovery_plans ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE infra_recovery_plans ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE infra_recovery_plans ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_infra_recovery_plans_plan_code ON infra_recovery_plans (plan_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_infra_recovery_plans_plan_code'
  ) THEN
    ALTER TABLE infra_recovery_plans
      ADD CONSTRAINT uq_infra_recovery_plans_plan_code UNIQUE (plan_code);
  END IF;
END $$;


-- ===== infra_recovery_reports =====
CREATE TABLE IF NOT EXISTS infra_recovery_reports (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE infra_recovery_reports ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE infra_recovery_reports ADD COLUMN IF NOT EXISTS plan_id VARCHAR(36);
ALTER TABLE infra_recovery_reports ADD COLUMN IF NOT EXISTS report_code VARCHAR(50);
ALTER TABLE infra_recovery_reports ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'COMPLETED';
ALTER TABLE infra_recovery_reports ADD COLUMN IF NOT EXISTS summary_json TEXT DEFAULT '{}';
ALTER TABLE infra_recovery_reports ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_infra_recovery_reports_report_code ON infra_recovery_reports (report_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_infra_recovery_reports_report_code'
  ) THEN
    ALTER TABLE infra_recovery_reports
      ADD CONSTRAINT uq_infra_recovery_reports_report_code UNIQUE (report_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.infra_recovery_plans') IS NULL THEN
    RAISE NOTICE 'infra_recovery_plans missing — skip FK fk_infra_recovery_reports_plan_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_infra_recovery_reports_plan_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE infra_recovery_reports
    ADD CONSTRAINT fk_infra_recovery_reports_plan_id
    FOREIGN KEY (plan_id) REFERENCES infra_recovery_plans (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_infra_recovery_reports_plan_id: %', SQLERRM;
END $$;

-- ===== infra_recovery_tests =====
CREATE TABLE IF NOT EXISTS infra_recovery_tests (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE infra_recovery_tests ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE infra_recovery_tests ADD COLUMN IF NOT EXISTS plan_id VARCHAR(36);
ALTER TABLE infra_recovery_tests ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE infra_recovery_tests ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PASSED';
ALTER TABLE infra_recovery_tests ADD COLUMN IF NOT EXISTS mode VARCHAR(50) DEFAULT 'DRY_RUN';
ALTER TABLE infra_recovery_tests ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_infra_recovery_tests_test_code ON infra_recovery_tests (test_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_infra_recovery_tests_test_code'
  ) THEN
    ALTER TABLE infra_recovery_tests
      ADD CONSTRAINT uq_infra_recovery_tests_test_code UNIQUE (test_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.infra_recovery_plans') IS NULL THEN
    RAISE NOTICE 'infra_recovery_plans missing — skip FK fk_infra_recovery_tests_plan_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_infra_recovery_tests_plan_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE infra_recovery_tests
    ADD CONSTRAINT fk_infra_recovery_tests_plan_id
    FOREIGN KEY (plan_id) REFERENCES infra_recovery_plans (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_infra_recovery_tests_plan_id: %', SQLERRM;
END $$;

-- ===== integration_audit_logs =====
CREATE TABLE IF NOT EXISTS integration_audit_logs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_audit_logs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_audit_logs ADD COLUMN IF NOT EXISTS connection_id VARCHAR(36);
ALTER TABLE integration_audit_logs ADD COLUMN IF NOT EXISTS message_id VARCHAR(36);
ALTER TABLE integration_audit_logs ADD COLUMN IF NOT EXISTS action VARCHAR(100);
ALTER TABLE integration_audit_logs ADD COLUMN IF NOT EXISTS detail TEXT;
ALTER TABLE integration_audit_logs ADD COLUMN IF NOT EXISTS actor_email VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE integration_audit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== integration_connections =====
CREATE TABLE IF NOT EXISTS integration_connections (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_connections ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_connections ADD COLUMN IF NOT EXISTS connection_code VARCHAR(50);
ALTER TABLE integration_connections ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE integration_connections ADD COLUMN IF NOT EXISTS protocol VARCHAR(50) DEFAULT 'HL7_FHIR';
ALTER TABLE integration_connections ADD COLUMN IF NOT EXISTS auth_type VARCHAR(50) DEFAULT 'API_KEY';
ALTER TABLE integration_connections ADD COLUMN IF NOT EXISTS config_json TEXT DEFAULT '{}';
ALTER TABLE integration_connections ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE integration_connections ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE integration_connections ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_integration_connections_connection_code ON integration_connections (connection_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_integration_connections_connection_code'
  ) THEN
    ALTER TABLE integration_connections
      ADD CONSTRAINT uq_integration_connections_connection_code UNIQUE (connection_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.integration_partners') IS NULL THEN
    RAISE NOTICE 'integration_partners missing — skip FK fk_integration_connections_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_integration_connections_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE integration_connections
    ADD CONSTRAINT fk_integration_connections_partner_id
    FOREIGN KEY (partner_id) REFERENCES integration_partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_integration_connections_partner_id: %', SQLERRM;
END $$;

-- ===== integration_connectors =====
CREATE TABLE IF NOT EXISTS integration_connectors (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_connectors ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_connectors ADD COLUMN IF NOT EXISTS connector_code VARCHAR(50);
ALTER TABLE integration_connectors ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE integration_connectors ADD COLUMN IF NOT EXISTS adapter_type VARCHAR(50);
ALTER TABLE integration_connectors ADD COLUMN IF NOT EXISTS config_json TEXT DEFAULT '{}';
ALTER TABLE integration_connectors ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE integration_connectors ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_integration_connectors_connector_code ON integration_connectors (connector_code);
CREATE INDEX IF NOT EXISTS ix_integration_connectors_adapter_type ON integration_connectors (adapter_type);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_integration_connectors_connector_code'
  ) THEN
    ALTER TABLE integration_connectors
      ADD CONSTRAINT uq_integration_connectors_connector_code UNIQUE (connector_code);
  END IF;
END $$;


-- ===== integration_dead_letters =====
CREATE TABLE IF NOT EXISTS integration_dead_letters (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_dead_letters ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_dead_letters ADD COLUMN IF NOT EXISTS job_id VARCHAR(36);
ALTER TABLE integration_dead_letters ADD COLUMN IF NOT EXISTS reason TEXT;
ALTER TABLE integration_dead_letters ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE integration_dead_letters ADD COLUMN IF NOT EXISTS replayed BOOLEAN DEFAULT FALSE;
ALTER TABLE integration_dead_letters ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.integration_jobs') IS NULL THEN
    RAISE NOTICE 'integration_jobs missing — skip FK fk_integration_dead_letters_job_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_integration_dead_letters_job_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE integration_dead_letters
    ADD CONSTRAINT fk_integration_dead_letters_job_id
    FOREIGN KEY (job_id) REFERENCES integration_jobs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_integration_dead_letters_job_id: %', SQLERRM;
END $$;

-- ===== integration_domain_events =====
CREATE TABLE IF NOT EXISTS integration_domain_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_domain_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_domain_events ADD COLUMN IF NOT EXISTS event_code VARCHAR(50);
ALTER TABLE integration_domain_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE integration_domain_events ADD COLUMN IF NOT EXISTS source VARCHAR(100) DEFAULT 'dxcon';
ALTER TABLE integration_domain_events ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(100);
ALTER TABLE integration_domain_events ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE integration_domain_events ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PUBLISHED';
ALTER TABLE integration_domain_events ADD COLUMN IF NOT EXISTS published_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE integration_domain_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_integration_domain_events_event_code ON integration_domain_events (event_code);
CREATE INDEX IF NOT EXISTS ix_integration_domain_events_event_type ON integration_domain_events (event_type);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_integration_domain_events_event_code'
  ) THEN
    ALTER TABLE integration_domain_events
      ADD CONSTRAINT uq_integration_domain_events_event_code UNIQUE (event_code);
  END IF;
END $$;


-- ===== integration_event_delivery_logs =====
CREATE TABLE IF NOT EXISTS integration_event_delivery_logs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_event_delivery_logs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_event_delivery_logs ADD COLUMN IF NOT EXISTS event_id VARCHAR(36);
ALTER TABLE integration_event_delivery_logs ADD COLUMN IF NOT EXISTS handler_name VARCHAR(100);
ALTER TABLE integration_event_delivery_logs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'OK';
ALTER TABLE integration_event_delivery_logs ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE integration_event_delivery_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_integration_event_delivery_logs_event_id ON integration_event_delivery_logs (event_id);



-- ===== integration_job_attempts =====
CREATE TABLE IF NOT EXISTS integration_job_attempts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_job_attempts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_job_attempts ADD COLUMN IF NOT EXISTS job_id VARCHAR(36);
ALTER TABLE integration_job_attempts ADD COLUMN IF NOT EXISTS attempt_number INTEGER DEFAULT 1;
ALTER TABLE integration_job_attempts ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE integration_job_attempts ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE integration_job_attempts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.integration_jobs') IS NULL THEN
    RAISE NOTICE 'integration_jobs missing — skip FK fk_integration_job_attempts_job_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_integration_job_attempts_job_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE integration_job_attempts
    ADD CONSTRAINT fk_integration_job_attempts_job_id
    FOREIGN KEY (job_id) REFERENCES integration_jobs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_integration_job_attempts_job_id: %', SQLERRM;
END $$;

-- ===== integration_jobs =====
CREATE TABLE IF NOT EXISTS integration_jobs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_jobs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_jobs ADD COLUMN IF NOT EXISTS job_code VARCHAR(50);
ALTER TABLE integration_jobs ADD COLUMN IF NOT EXISTS adapter_type VARCHAR(50);
ALTER TABLE integration_jobs ADD COLUMN IF NOT EXISTS direction VARCHAR(20) DEFAULT 'OUTBOUND';
ALTER TABLE integration_jobs ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE integration_jobs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE integration_jobs ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
ALTER TABLE integration_jobs ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3;
ALTER TABLE integration_jobs ADD COLUMN IF NOT EXISTS last_error TEXT;
ALTER TABLE integration_jobs ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE integration_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_integration_jobs_job_code ON integration_jobs (job_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_integration_jobs_job_code'
  ) THEN
    ALTER TABLE integration_jobs
      ADD CONSTRAINT uq_integration_jobs_job_code UNIQUE (job_code);
  END IF;
END $$;


-- ===== integration_messages =====
CREATE TABLE IF NOT EXISTS integration_messages (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_messages ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_messages ADD COLUMN IF NOT EXISTS message_code VARCHAR(50);
ALTER TABLE integration_messages ADD COLUMN IF NOT EXISTS connection_id VARCHAR(36);
ALTER TABLE integration_messages ADD COLUMN IF NOT EXISTS message_type VARCHAR(50);
ALTER TABLE integration_messages ADD COLUMN IF NOT EXISTS direction VARCHAR(20) DEFAULT 'INBOUND';
ALTER TABLE integration_messages ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE integration_messages ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'RECEIVED';
ALTER TABLE integration_messages ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE integration_messages ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_integration_messages_message_code ON integration_messages (message_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_integration_messages_message_code'
  ) THEN
    ALTER TABLE integration_messages
      ADD CONSTRAINT uq_integration_messages_message_code UNIQUE (message_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.integration_connections') IS NULL THEN
    RAISE NOTICE 'integration_connections missing — skip FK fk_integration_messages_connection_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_integration_messages_connection_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE integration_messages
    ADD CONSTRAINT fk_integration_messages_connection_id
    FOREIGN KEY (connection_id) REFERENCES integration_connections (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_integration_messages_connection_id: %', SQLERRM;
END $$;

-- ===== integration_partners =====
CREATE TABLE IF NOT EXISTS integration_partners (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_partners ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_partners ADD COLUMN IF NOT EXISTS partner_code VARCHAR(50);
ALTER TABLE integration_partners ADD COLUMN IF NOT EXISTS partner_name VARCHAR(255);
ALTER TABLE integration_partners ADD COLUMN IF NOT EXISTS integration_type VARCHAR(50);
ALTER TABLE integration_partners ADD COLUMN IF NOT EXISTS endpoint_url VARCHAR(500);
ALTER TABLE integration_partners ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE integration_partners ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_integration_partners_partner_code ON integration_partners (partner_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_integration_partners_partner_code'
  ) THEN
    ALTER TABLE integration_partners
      ADD CONSTRAINT uq_integration_partners_partner_code UNIQUE (partner_code);
  END IF;
END $$;


-- ===== integration_platform_audit_logs =====
CREATE TABLE IF NOT EXISTS integration_platform_audit_logs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_platform_audit_logs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_platform_audit_logs ADD COLUMN IF NOT EXISTS action VARCHAR(100);
ALTER TABLE integration_platform_audit_logs ADD COLUMN IF NOT EXISTS resource_type VARCHAR(100);
ALTER TABLE integration_platform_audit_logs ADD COLUMN IF NOT EXISTS resource_id VARCHAR(100);
ALTER TABLE integration_platform_audit_logs ADD COLUMN IF NOT EXISTS actor VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE integration_platform_audit_logs ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE integration_platform_audit_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_integration_platform_audit_logs_action ON integration_platform_audit_logs (action);



-- ===== integration_plugin_states =====
CREATE TABLE IF NOT EXISTS integration_plugin_states (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_plugin_states ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_plugin_states ADD COLUMN IF NOT EXISTS plugin_id VARCHAR(100);
ALTER TABLE integration_plugin_states ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE integration_plugin_states ADD COLUMN IF NOT EXISTS version VARCHAR(50) DEFAULT '1.0.0';
ALTER TABLE integration_plugin_states ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'DISABLED';
ALTER TABLE integration_plugin_states ADD COLUMN IF NOT EXISTS config_json TEXT DEFAULT '{}';
ALTER TABLE integration_plugin_states ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_integration_plugin_states_plugin_id ON integration_plugin_states (plugin_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_integration_plugin_states_plugin_id'
  ) THEN
    ALTER TABLE integration_plugin_states
      ADD CONSTRAINT uq_integration_plugin_states_plugin_id UNIQUE (plugin_id);
  END IF;
END $$;


-- ===== integration_webhook_deliveries =====
CREATE TABLE IF NOT EXISTS integration_webhook_deliveries (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS delivery_code VARCHAR(50);
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS webhook_id VARCHAR(36);
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS webhook_event_id VARCHAR(36);
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS signature VARCHAR(255);
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS response_code INTEGER;
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS failure_reason TEXT;
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS attempt_count INTEGER DEFAULT 0;
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3;
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE integration_webhook_deliveries ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_integration_webhook_deliveries_delivery_code ON integration_webhook_deliveries (delivery_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_integration_webhook_deliveries_delivery_code'
  ) THEN
    ALTER TABLE integration_webhook_deliveries
      ADD CONSTRAINT uq_integration_webhook_deliveries_delivery_code UNIQUE (delivery_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.integration_webhook_events') IS NULL THEN
    RAISE NOTICE 'integration_webhook_events missing — skip FK fk_integration_webhook_deliveries_webhook_event_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_integration_webhook_deliveries_webhook_event_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE integration_webhook_deliveries
    ADD CONSTRAINT fk_integration_webhook_deliveries_webhook_event_id
    FOREIGN KEY (webhook_event_id) REFERENCES integration_webhook_events (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_integration_webhook_deliveries_webhook_event_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.integration_webhook_endpoints') IS NULL THEN
    RAISE NOTICE 'integration_webhook_endpoints missing — skip FK fk_integration_webhook_deliveries_webhook_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_integration_webhook_deliveries_webhook_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE integration_webhook_deliveries
    ADD CONSTRAINT fk_integration_webhook_deliveries_webhook_id
    FOREIGN KEY (webhook_id) REFERENCES integration_webhook_endpoints (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_integration_webhook_deliveries_webhook_id: %', SQLERRM;
END $$;

-- ===== integration_webhook_endpoints =====
CREATE TABLE IF NOT EXISTS integration_webhook_endpoints (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_webhook_endpoints ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_webhook_endpoints ADD COLUMN IF NOT EXISTS endpoint_code VARCHAR(50);
ALTER TABLE integration_webhook_endpoints ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE integration_webhook_endpoints ADD COLUMN IF NOT EXISTS target_url VARCHAR(500);
ALTER TABLE integration_webhook_endpoints ADD COLUMN IF NOT EXISTS event_types_json TEXT DEFAULT '[]';
ALTER TABLE integration_webhook_endpoints ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE integration_webhook_endpoints ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_integration_webhook_endpoints_endpoint_code ON integration_webhook_endpoints (endpoint_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_integration_webhook_endpoints_endpoint_code'
  ) THEN
    ALTER TABLE integration_webhook_endpoints
      ADD CONSTRAINT uq_integration_webhook_endpoints_endpoint_code UNIQUE (endpoint_code);
  END IF;
END $$;


-- ===== integration_webhook_events =====
CREATE TABLE IF NOT EXISTS integration_webhook_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_webhook_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_webhook_events ADD COLUMN IF NOT EXISTS event_code VARCHAR(50);
ALTER TABLE integration_webhook_events ADD COLUMN IF NOT EXISTS webhook_id VARCHAR(36);
ALTER TABLE integration_webhook_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE integration_webhook_events ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE integration_webhook_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_integration_webhook_events_event_code ON integration_webhook_events (event_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_integration_webhook_events_event_code'
  ) THEN
    ALTER TABLE integration_webhook_events
      ADD CONSTRAINT uq_integration_webhook_events_event_code UNIQUE (event_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.integration_webhook_endpoints') IS NULL THEN
    RAISE NOTICE 'integration_webhook_endpoints missing — skip FK fk_integration_webhook_events_webhook_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_integration_webhook_events_webhook_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE integration_webhook_events
    ADD CONSTRAINT fk_integration_webhook_events_webhook_id
    FOREIGN KEY (webhook_id) REFERENCES integration_webhook_endpoints (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_integration_webhook_events_webhook_id: %', SQLERRM;
END $$;

-- ===== integration_webhook_secrets =====
CREATE TABLE IF NOT EXISTS integration_webhook_secrets (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE integration_webhook_secrets ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE integration_webhook_secrets ADD COLUMN IF NOT EXISTS webhook_id VARCHAR(36);
ALTER TABLE integration_webhook_secrets ADD COLUMN IF NOT EXISTS secret_value VARCHAR(255);
ALTER TABLE integration_webhook_secrets ADD COLUMN IF NOT EXISTS algorithm VARCHAR(50) DEFAULT 'HMAC-SHA256';
ALTER TABLE integration_webhook_secrets ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE integration_webhook_secrets ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.integration_webhook_endpoints') IS NULL THEN
    RAISE NOTICE 'integration_webhook_endpoints missing — skip FK fk_integration_webhook_secrets_webhook_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_integration_webhook_secrets_webhook_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE integration_webhook_secrets
    ADD CONSTRAINT fk_integration_webhook_secrets_webhook_id
    FOREIGN KEY (webhook_id) REFERENCES integration_webhook_endpoints (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_integration_webhook_secrets_webhook_id: %', SQLERRM;
END $$;

-- ===== interpretation_results =====
CREATE TABLE IF NOT EXISTS interpretation_results (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS lab_result_item_id VARCHAR(36);
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS result_value VARCHAR(255);
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS flag VARCHAR(20) DEFAULT 'NORMAL';
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS reference_range_used VARCHAR(255);
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS is_critical BOOLEAN DEFAULT FALSE;
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) DEFAULT 'LOW';
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS interpretation_en TEXT;
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS interpretation_vi TEXT;
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS recommendation_en TEXT;
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS recommendation_vi TEXT;
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS rule_id VARCHAR(36);
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS template_code VARCHAR(50);
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS template_version INTEGER;
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE interpretation_results ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.interpretation_rules') IS NULL THEN
    RAISE NOTICE 'interpretation_rules missing — skip FK fk_interpretation_results_rule_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_interpretation_results_rule_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE interpretation_results
    ADD CONSTRAINT fk_interpretation_results_rule_id
    FOREIGN KEY (rule_id) REFERENCES interpretation_rules (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_interpretation_results_rule_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.lab_result_items') IS NULL THEN
    RAISE NOTICE 'lab_result_items missing — skip FK fk_interpretation_results_lab_result_item_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_interpretation_results_lab_result_item_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE interpretation_results
    ADD CONSTRAINT fk_interpretation_results_lab_result_item_id
    FOREIGN KEY (lab_result_item_id) REFERENCES lab_result_items (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_interpretation_results_lab_result_item_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.lab_results') IS NULL THEN
    RAISE NOTICE 'lab_results missing — skip FK fk_interpretation_results_lab_result_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_interpretation_results_lab_result_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE interpretation_results
    ADD CONSTRAINT fk_interpretation_results_lab_result_id
    FOREIGN KEY (lab_result_id) REFERENCES lab_results (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_interpretation_results_lab_result_id: %', SQLERRM;
END $$;

-- ===== interpretation_rules =====
CREATE TABLE IF NOT EXISTS interpretation_rules (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS rule_code VARCHAR(50);
ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS test_name_pattern VARCHAR(255);
ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS condition_flag VARCHAR(20) DEFAULT 'ANY';
ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS risk_level VARCHAR(20) DEFAULT 'LOW';
ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS finding_en TEXT;
ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS finding_vi TEXT;
ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS recommendation_en TEXT;
ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS recommendation_vi TEXT;
ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 100;
ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE interpretation_rules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_interpretation_rules_rule_code ON interpretation_rules (rule_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_interpretation_rules_rule_code'
  ) THEN
    ALTER TABLE interpretation_rules
      ADD CONSTRAINT uq_interpretation_rules_rule_code UNIQUE (rule_code);
  END IF;
END $$;


-- ===== interpretation_templates =====
CREATE TABLE IF NOT EXISTS interpretation_templates (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE interpretation_templates ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE interpretation_templates ADD COLUMN IF NOT EXISTS template_code VARCHAR(50);
ALTER TABLE interpretation_templates ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE interpretation_templates ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'en';
ALTER TABLE interpretation_templates ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE interpretation_templates ADD COLUMN IF NOT EXISTS body_template TEXT;
ALTER TABLE interpretation_templates ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE interpretation_templates ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_interp_template_version_lang'
  ) THEN
    ALTER TABLE interpretation_templates
      ADD CONSTRAINT uq_interp_template_version_lang UNIQUE (template_code, version, language);
  END IF;
END $$;


-- ===== intg_api_credentials =====
CREATE TABLE IF NOT EXISTS intg_api_credentials (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE intg_api_credentials ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE intg_api_credentials ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE intg_api_credentials ADD COLUMN IF NOT EXISTS name VARCHAR(100);
ALTER TABLE intg_api_credentials ADD COLUMN IF NOT EXISTS credential_type VARCHAR(30);
ALTER TABLE intg_api_credentials ADD COLUMN IF NOT EXISTS key_hash VARCHAR(128);
ALTER TABLE intg_api_credentials ADD COLUMN IF NOT EXISTS secret_reference VARCHAR(255);
ALTER TABLE intg_api_credentials ADD COLUMN IF NOT EXISTS scopes_json TEXT DEFAULT '[]';
ALTER TABLE intg_api_credentials ADD COLUMN IF NOT EXISTS ip_allowlist_json TEXT;
ALTER TABLE intg_api_credentials ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE intg_api_credentials ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE intg_api_credentials ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_intg_api_credentials_organization_id ON intg_api_credentials (organization_id);



-- ===== intg_audit_events =====
CREATE TABLE IF NOT EXISTS intg_audit_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE intg_audit_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE intg_audit_events ADD COLUMN IF NOT EXISTS action VARCHAR(80);
ALTER TABLE intg_audit_events ADD COLUMN IF NOT EXISTS actor VARCHAR(255);
ALTER TABLE intg_audit_events ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE intg_audit_events ADD COLUMN IF NOT EXISTS connector_id VARCHAR(36);
ALTER TABLE intg_audit_events ADD COLUMN IF NOT EXISTS message_id VARCHAR(36);
ALTER TABLE intg_audit_events ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(255);
ALTER TABLE intg_audit_events ADD COLUMN IF NOT EXISTS outcome VARCHAR(20);
ALTER TABLE intg_audit_events ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE intg_audit_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_intg_audit_events_action ON intg_audit_events (action);
CREATE INDEX IF NOT EXISTS ix_intg_audit_events_organization_id ON intg_audit_events (organization_id);



-- ===== intg_connectors =====
CREATE TABLE IF NOT EXISTS intg_connectors (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS connector_code VARCHAR(80);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS connector_name VARCHAR(255);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS connector_type VARCHAR(30);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS vendor VARCHAR(100);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS protocol VARCHAR(30);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS laboratory_id VARCHAR(36);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS clinic_id VARCHAR(36);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS base_url VARCHAR(500);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS direction VARCHAR(20) DEFAULT 'INBOUND';
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS authentication_type VARCHAR(30);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS secret_reference VARCHAR(255);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'DRAFT';
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS environment VARCHAR(20) DEFAULT 'production';
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS lis_connector_id VARCHAR(36);
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS last_success_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS last_failure_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE intg_connectors ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_intg_connectors_connector_code ON intg_connectors (connector_code);
CREATE INDEX IF NOT EXISTS ix_intg_connectors_organization_id ON intg_connectors (organization_id);



-- ===== intg_dead_letters =====
CREATE TABLE IF NOT EXISTS intg_dead_letters (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE intg_dead_letters ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE intg_dead_letters ADD COLUMN IF NOT EXISTS message_id VARCHAR(36);
ALTER TABLE intg_dead_letters ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE intg_dead_letters ADD COLUMN IF NOT EXISTS connector_id VARCHAR(36);
ALTER TABLE intg_dead_letters ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
ALTER TABLE intg_dead_letters ADD COLUMN IF NOT EXISTS maximum_retries INTEGER DEFAULT 5;
ALTER TABLE intg_dead_letters ADD COLUMN IF NOT EXISTS last_error TEXT;
ALTER TABLE intg_dead_letters ADD COLUMN IF NOT EXISTS retry_strategy VARCHAR(30) DEFAULT 'EXPONENTIAL_BACKOFF';
ALTER TABLE intg_dead_letters ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE intg_dead_letters ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'DEAD_LETTER';
ALTER TABLE intg_dead_letters ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== intg_delivery_attempts =====
CREATE TABLE IF NOT EXISTS intg_delivery_attempts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE intg_delivery_attempts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE intg_delivery_attempts ADD COLUMN IF NOT EXISTS subscription_id VARCHAR(36);
ALTER TABLE intg_delivery_attempts ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE intg_delivery_attempts ADD COLUMN IF NOT EXISTS delivery_id VARCHAR(80);
ALTER TABLE intg_delivery_attempts ADD COLUMN IF NOT EXISTS event_type VARCHAR(80);
ALTER TABLE intg_delivery_attempts ADD COLUMN IF NOT EXISTS payload_hash VARCHAR(64);
ALTER TABLE intg_delivery_attempts ADD COLUMN IF NOT EXISTS status VARCHAR(20);
ALTER TABLE intg_delivery_attempts ADD COLUMN IF NOT EXISTS attempt_number INTEGER DEFAULT 1;
ALTER TABLE intg_delivery_attempts ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE intg_delivery_attempts ADD COLUMN IF NOT EXISTS last_error TEXT;
ALTER TABLE intg_delivery_attempts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_intg_delivery_attempts_subscription_id ON intg_delivery_attempts (subscription_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_intg_delivery_attempts_delivery_id ON intg_delivery_attempts (delivery_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_intg_delivery_attempts_delivery_id'
  ) THEN
    ALTER TABLE intg_delivery_attempts
      ADD CONSTRAINT uq_intg_delivery_attempts_delivery_id UNIQUE (delivery_id);
  END IF;
END $$;


-- ===== intg_external_mappings =====
CREATE TABLE IF NOT EXISTS intg_external_mappings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE intg_external_mappings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE intg_external_mappings ADD COLUMN IF NOT EXISTS connector_id VARCHAR(36);
ALTER TABLE intg_external_mappings ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE intg_external_mappings ADD COLUMN IF NOT EXISTS mapping_kind VARCHAR(30);
ALTER TABLE intg_external_mappings ADD COLUMN IF NOT EXISTS external_code VARCHAR(100);
ALTER TABLE intg_external_mappings ADD COLUMN IF NOT EXISTS internal_code VARCHAR(100);
ALTER TABLE intg_external_mappings ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE intg_external_mappings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_intg_ext_map'
  ) THEN
    ALTER TABLE intg_external_mappings
      ADD CONSTRAINT uq_intg_ext_map UNIQUE (connector_id, mapping_kind, external_code);
  END IF;
END $$;


-- ===== intg_mapping_rules =====
CREATE TABLE IF NOT EXISTS intg_mapping_rules (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE intg_mapping_rules ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE intg_mapping_rules ADD COLUMN IF NOT EXISTS connector_id VARCHAR(36);
ALTER TABLE intg_mapping_rules ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE intg_mapping_rules ADD COLUMN IF NOT EXISTS external_field VARCHAR(100);
ALTER TABLE intg_mapping_rules ADD COLUMN IF NOT EXISTS canonical_field VARCHAR(100);
ALTER TABLE intg_mapping_rules ADD COLUMN IF NOT EXISTS transformation_type VARCHAR(30) DEFAULT 'DIRECT';
ALTER TABLE intg_mapping_rules ADD COLUMN IF NOT EXISTS default_value VARCHAR(255);
ALTER TABLE intg_mapping_rules ADD COLUMN IF NOT EXISTS required BOOLEAN DEFAULT FALSE;
ALTER TABLE intg_mapping_rules ADD COLUMN IF NOT EXISTS value_mapping_json TEXT;
ALTER TABLE intg_mapping_rules ADD COLUMN IF NOT EXISTS date_format VARCHAR(50);
ALTER TABLE intg_mapping_rules ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE intg_mapping_rules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_intg_mapping_rules_connector_id ON intg_mapping_rules (connector_id);



-- ===== intg_messages =====
CREATE TABLE IF NOT EXISTS intg_messages (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS message_id VARCHAR(80);
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS connector_id VARCHAR(36);
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS direction VARCHAR(20);
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS message_type VARCHAR(50);
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS external_message_id VARCHAR(255);
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(255);
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS payload_format VARCHAR(20);
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS payload_hash VARCHAR(64);
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'RECEIVED';
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS received_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS error_code VARCHAR(50);
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS payload_preview TEXT;
ALTER TABLE intg_messages ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_intg_messages_message_id ON intg_messages (message_id);
CREATE INDEX IF NOT EXISTS ix_intg_messages_connector_id ON intg_messages (connector_id);
CREATE INDEX IF NOT EXISTS ix_intg_messages_organization_id ON intg_messages (organization_id);
CREATE INDEX IF NOT EXISTS ix_intg_messages_payload_hash ON intg_messages (payload_hash);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_intg_msg_dedup'
  ) THEN
    ALTER TABLE intg_messages
      ADD CONSTRAINT uq_intg_msg_dedup UNIQUE (connector_id, external_message_id, message_type);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_intg_messages_message_id'
  ) THEN
    ALTER TABLE intg_messages
      ADD CONSTRAINT uq_intg_messages_message_id UNIQUE (message_id);
  END IF;
END $$;


-- ===== intg_webhook_subscriptions =====
CREATE TABLE IF NOT EXISTS intg_webhook_subscriptions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE intg_webhook_subscriptions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE intg_webhook_subscriptions ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE intg_webhook_subscriptions ADD COLUMN IF NOT EXISTS connector_id VARCHAR(36);
ALTER TABLE intg_webhook_subscriptions ADD COLUMN IF NOT EXISTS event_type VARCHAR(80);
ALTER TABLE intg_webhook_subscriptions ADD COLUMN IF NOT EXISTS endpoint_url VARCHAR(500);
ALTER TABLE intg_webhook_subscriptions ADD COLUMN IF NOT EXISTS secret_reference VARCHAR(255);
ALTER TABLE intg_webhook_subscriptions ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE intg_webhook_subscriptions ADD COLUMN IF NOT EXISTS retry_policy VARCHAR(30) DEFAULT 'EXPONENTIAL_BACKOFF';
ALTER TABLE intg_webhook_subscriptions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_intg_webhook_subscriptions_organization_id ON intg_webhook_subscriptions (organization_id);



-- ===== invoice_items =====
CREATE TABLE IF NOT EXISTS invoice_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE invoice_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE invoice_items ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE invoice_items ADD COLUMN IF NOT EXISTS description VARCHAR(255);
ALTER TABLE invoice_items ADD COLUMN IF NOT EXISTS service_code VARCHAR(50);
ALTER TABLE invoice_items ADD COLUMN IF NOT EXISTS quantity INTEGER DEFAULT 1;
ALTER TABLE invoice_items ADD COLUMN IF NOT EXISTS unit_price FLOAT DEFAULT 0;
ALTER TABLE invoice_items ADD COLUMN IF NOT EXISTS line_total FLOAT DEFAULT 0;
ALTER TABLE invoice_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.invoices') IS NULL THEN
    RAISE NOTICE 'invoices missing — skip FK fk_invoice_items_invoice_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_invoice_items_invoice_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE invoice_items
    ADD CONSTRAINT fk_invoice_items_invoice_id
    FOREIGN KEY (invoice_id) REFERENCES invoices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_invoice_items_invoice_id: %', SQLERRM;
END $$;

-- ===== invoices =====
CREATE TABLE IF NOT EXISTS invoices (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE invoices ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS invoice_no VARCHAR(50);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS company_id VARCHAR(36);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS total_amount FLOAT DEFAULT 0;
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50) DEFAULT 'UNPAID';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS billing_status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE invoices ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_invoices_invoice_no ON invoices (invoice_no);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_invoices_invoice_no'
  ) THEN
    ALTER TABLE invoices
      ADD CONSTRAINT uq_invoices_invoice_no UNIQUE (invoice_no);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_invoices_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_invoices_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE invoices
    ADD CONSTRAINT fk_invoices_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_invoices_medical_order_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_invoices_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_invoices_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE invoices
    ADD CONSTRAINT fk_invoices_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_invoices_partner_id: %', SQLERRM;
END $$;

-- ===== iot_devices =====
CREATE TABLE IF NOT EXISTS iot_devices (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS device_code VARCHAR(50);
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS device_type VARCHAR(50) DEFAULT 'COLD_BOX';
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS serial_number VARCHAR(100);
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_iot_devices_device_code ON iot_devices (device_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_iot_devices_device_code'
  ) THEN
    ALTER TABLE iot_devices
      ADD CONSTRAINT uq_iot_devices_device_code UNIQUE (device_code);
  END IF;
END $$;


-- ===== iot_offline_event_buffer =====
CREATE TABLE IF NOT EXISTS iot_offline_event_buffer (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE iot_offline_event_buffer ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE iot_offline_event_buffer ADD COLUMN IF NOT EXISTS device_id VARCHAR(36);
ALTER TABLE iot_offline_event_buffer ADD COLUMN IF NOT EXISTS adapter_type VARCHAR(50) DEFAULT 'GENERIC';
ALTER TABLE iot_offline_event_buffer ADD COLUMN IF NOT EXISTS event_type VARCHAR(50);
ALTER TABLE iot_offline_event_buffer ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE iot_offline_event_buffer ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'PENDING';
ALTER TABLE iot_offline_event_buffer ADD COLUMN IF NOT EXISTS buffered_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE iot_offline_event_buffer ADD COLUMN IF NOT EXISTS synced_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_iot_offline_event_buffer_device_id ON iot_offline_event_buffer (device_id);
CREATE INDEX IF NOT EXISTS ix_iot_offline_event_buffer_status ON iot_offline_event_buffer (status);


DO $$
BEGIN
  IF to_regclass('public.iot_devices') IS NULL THEN
    RAISE NOTICE 'iot_devices missing — skip FK fk_iot_offline_event_buffer_device_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_iot_offline_event_buffer_device_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE iot_offline_event_buffer
    ADD CONSTRAINT fk_iot_offline_event_buffer_device_id
    FOREIGN KEY (device_id) REFERENCES iot_devices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_iot_offline_event_buffer_device_id: %', SQLERRM;
END $$;

-- ===== kpi_events =====
CREATE TABLE IF NOT EXISTS kpi_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE kpi_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE kpi_events ADD COLUMN IF NOT EXISTS event_code VARCHAR(50);
ALTER TABLE kpi_events ADD COLUMN IF NOT EXISTS kpi_code VARCHAR(50);
ALTER TABLE kpi_events ADD COLUMN IF NOT EXISTS kpi_value FLOAT DEFAULT 0;
ALTER TABLE kpi_events ADD COLUMN IF NOT EXISTS dimension VARCHAR(50);
ALTER TABLE kpi_events ADD COLUMN IF NOT EXISTS reference_id VARCHAR(36);
ALTER TABLE kpi_events ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE kpi_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_kpi_events_event_code ON kpi_events (event_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_kpi_events_event_code'
  ) THEN
    ALTER TABLE kpi_events
      ADD CONSTRAINT uq_kpi_events_event_code UNIQUE (event_code);
  END IF;
END $$;


-- ===== kpi_records =====
CREATE TABLE IF NOT EXISTS kpi_records (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE kpi_records ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE kpi_records ADD COLUMN IF NOT EXISTS record_code VARCHAR(50);
ALTER TABLE kpi_records ADD COLUMN IF NOT EXISTS period_type VARCHAR(20);
ALTER TABLE kpi_records ADD COLUMN IF NOT EXISTS period_start TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE kpi_records ADD COLUMN IF NOT EXISTS period_end TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE kpi_records ADD COLUMN IF NOT EXISTS kpi_code VARCHAR(50);
ALTER TABLE kpi_records ADD COLUMN IF NOT EXISTS kpi_value FLOAT DEFAULT 0;
ALTER TABLE kpi_records ADD COLUMN IF NOT EXISTS dimension VARCHAR(50);
ALTER TABLE kpi_records ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE kpi_records ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_kpi_records_record_code ON kpi_records (record_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_kpi_records_record_code'
  ) THEN
    ALTER TABLE kpi_records
      ADD CONSTRAINT uq_kpi_records_record_code UNIQUE (record_code);
  END IF;
END $$;


-- ===== lab_accession_records =====
CREATE TABLE IF NOT EXISTS lab_accession_records (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS accession_number VARCHAR(50);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS order_code VARCHAR(50);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS sample_code VARCHAR(50);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS patient_code VARCHAR(50);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS accessioned_by VARCHAR(255);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS accessioned_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS laboratory_id VARCHAR(36);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'active';
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS processing_status VARCHAR(40) DEFAULT 'accessioned';
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS bench_id VARCHAR(100);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS instrument_id VARCHAR(100);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS technician VARCHAR(255);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS identifiers_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS rejection_reason VARCHAR(80);
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS processing_started_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS processing_completed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_accession_records ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_accession_records_accession_number ON lab_accession_records (accession_number);
CREATE INDEX IF NOT EXISTS ix_lab_accession_records_order_code ON lab_accession_records (order_code);
CREATE INDEX IF NOT EXISTS ix_lab_accession_records_sample_code ON lab_accession_records (sample_code);



-- ===== lab_analytics =====
CREATE TABLE IF NOT EXISTS lab_analytics (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_analytics ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_analytics ADD COLUMN IF NOT EXISTS analytics_code VARCHAR(50);
ALTER TABLE lab_analytics ADD COLUMN IF NOT EXISTS period_start TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_analytics ADD COLUMN IF NOT EXISTS period_end TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_analytics ADD COLUMN IF NOT EXISTS lab_partner_id VARCHAR(36);
ALTER TABLE lab_analytics ADD COLUMN IF NOT EXISTS tests_total INTEGER DEFAULT 0;
ALTER TABLE lab_analytics ADD COLUMN IF NOT EXISTS tat_avg_hours FLOAT DEFAULT 0;
ALTER TABLE lab_analytics ADD COLUMN IF NOT EXISTS critical_rate FLOAT DEFAULT 0;
ALTER TABLE lab_analytics ADD COLUMN IF NOT EXISTS pending_reviews INTEGER DEFAULT 0;
ALTER TABLE lab_analytics ADD COLUMN IF NOT EXISTS metrics_json TEXT DEFAULT '{}';
ALTER TABLE lab_analytics ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_analytics_analytics_code ON lab_analytics (analytics_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_analytics_analytics_code'
  ) THEN
    ALTER TABLE lab_analytics
      ADD CONSTRAINT uq_lab_analytics_analytics_code UNIQUE (analytics_code);
  END IF;
END $$;


-- ===== lab_analyzer_queues =====
CREATE TABLE IF NOT EXISTS lab_analyzer_queues (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_analyzer_queues ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_analyzer_queues ADD COLUMN IF NOT EXISTS queue_code VARCHAR(50);
ALTER TABLE lab_analyzer_queues ADD COLUMN IF NOT EXISTS analyzer_id VARCHAR(36);
ALTER TABLE lab_analyzer_queues ADD COLUMN IF NOT EXISTS accession_id VARCHAR(36);
ALTER TABLE lab_analyzer_queues ADD COLUMN IF NOT EXISTS position INTEGER DEFAULT 0;
ALTER TABLE lab_analyzer_queues ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'QUEUED';
ALTER TABLE lab_analyzer_queues ADD COLUMN IF NOT EXISTS queued_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_analyzer_queues ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_analyzer_queues ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_analyzer_queues ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_analyzer_queues_queue_code ON lab_analyzer_queues (queue_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_analyzer_queues_queue_code'
  ) THEN
    ALTER TABLE lab_analyzer_queues
      ADD CONSTRAINT uq_lab_analyzer_queues_queue_code UNIQUE (queue_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.lab_sample_accessions') IS NULL THEN
    RAISE NOTICE 'lab_sample_accessions missing — skip FK fk_lab_analyzer_queues_accession_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_analyzer_queues_accession_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_analyzer_queues
    ADD CONSTRAINT fk_lab_analyzer_queues_accession_id
    FOREIGN KEY (accession_id) REFERENCES lab_sample_accessions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_analyzer_queues_accession_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.lab_analyzers') IS NULL THEN
    RAISE NOTICE 'lab_analyzers missing — skip FK fk_lab_analyzer_queues_analyzer_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_analyzer_queues_analyzer_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_analyzer_queues
    ADD CONSTRAINT fk_lab_analyzer_queues_analyzer_id
    FOREIGN KEY (analyzer_id) REFERENCES lab_analyzers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_analyzer_queues_analyzer_id: %', SQLERRM;
END $$;

-- ===== lab_analyzers =====
CREATE TABLE IF NOT EXISTS lab_analyzers (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS analyzer_code VARCHAR(50);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS model VARCHAR(100);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS manufacturer VARCHAR(100);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS lab_bench_id VARCHAR(36);
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS utilization_percent FLOAT DEFAULT 0;
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS last_run_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_analyzers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_analyzers_analyzer_code ON lab_analyzers (analyzer_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_analyzers_analyzer_code'
  ) THEN
    ALTER TABLE lab_analyzers
      ADD CONSTRAINT uq_lab_analyzers_analyzer_code UNIQUE (analyzer_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.lab_benches') IS NULL THEN
    RAISE NOTICE 'lab_benches missing — skip FK fk_lab_analyzers_lab_bench_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_analyzers_lab_bench_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_analyzers
    ADD CONSTRAINT fk_lab_analyzers_lab_bench_id
    FOREIGN KEY (lab_bench_id) REFERENCES lab_benches (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_analyzers_lab_bench_id: %', SQLERRM;
END $$;

-- ===== lab_benches =====
CREATE TABLE IF NOT EXISTS lab_benches (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_benches ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_benches ADD COLUMN IF NOT EXISTS bench_code VARCHAR(50);
ALTER TABLE lab_benches ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE lab_benches ADD COLUMN IF NOT EXISTS department VARCHAR(100);
ALTER TABLE lab_benches ADD COLUMN IF NOT EXISTS location VARCHAR(255);
ALTER TABLE lab_benches ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE lab_benches ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_benches_bench_code ON lab_benches (bench_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_benches_bench_code'
  ) THEN
    ALTER TABLE lab_benches
      ADD CONSTRAINT uq_lab_benches_bench_code UNIQUE (bench_code);
  END IF;
END $$;


-- ===== lab_critical_results =====
CREATE TABLE IF NOT EXISTS lab_critical_results (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_critical_results ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_critical_results ADD COLUMN IF NOT EXISTS critical_code VARCHAR(50);
ALTER TABLE lab_critical_results ADD COLUMN IF NOT EXISTS accession_id VARCHAR(36);
ALTER TABLE lab_critical_results ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE lab_critical_results ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE lab_critical_results ADD COLUMN IF NOT EXISTS result_value VARCHAR(100);
ALTER TABLE lab_critical_results ADD COLUMN IF NOT EXISTS critical_type VARCHAR(50) DEFAULT 'HIGH';
ALTER TABLE lab_critical_results ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'OPEN';
ALTER TABLE lab_critical_results ADD COLUMN IF NOT EXISTS notified_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_critical_results ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_critical_results ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_critical_results_critical_code ON lab_critical_results (critical_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_critical_results_critical_code'
  ) THEN
    ALTER TABLE lab_critical_results
      ADD CONSTRAINT uq_lab_critical_results_critical_code UNIQUE (critical_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.lab_sample_accessions') IS NULL THEN
    RAISE NOTICE 'lab_sample_accessions missing — skip FK fk_lab_critical_results_accession_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_critical_results_accession_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_critical_results
    ADD CONSTRAINT fk_lab_critical_results_accession_id
    FOREIGN KEY (accession_id) REFERENCES lab_sample_accessions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_critical_results_accession_id: %', SQLERRM;
END $$;

-- ===== lab_delta_checks =====
CREATE TABLE IF NOT EXISTS lab_delta_checks (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_delta_checks ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_delta_checks ADD COLUMN IF NOT EXISTS delta_code VARCHAR(50);
ALTER TABLE lab_delta_checks ADD COLUMN IF NOT EXISTS accession_id VARCHAR(36);
ALTER TABLE lab_delta_checks ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE lab_delta_checks ADD COLUMN IF NOT EXISTS previous_value FLOAT;
ALTER TABLE lab_delta_checks ADD COLUMN IF NOT EXISTS current_value FLOAT;
ALTER TABLE lab_delta_checks ADD COLUMN IF NOT EXISTS delta_percent FLOAT;
ALTER TABLE lab_delta_checks ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE lab_delta_checks ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(255);
ALTER TABLE lab_delta_checks ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_delta_checks_delta_code ON lab_delta_checks (delta_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_delta_checks_delta_code'
  ) THEN
    ALTER TABLE lab_delta_checks
      ADD CONSTRAINT uq_lab_delta_checks_delta_code UNIQUE (delta_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.lab_sample_accessions') IS NULL THEN
    RAISE NOTICE 'lab_sample_accessions missing — skip FK fk_lab_delta_checks_accession_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_delta_checks_accession_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_delta_checks
    ADD CONSTRAINT fk_lab_delta_checks_accession_id
    FOREIGN KEY (accession_id) REFERENCES lab_sample_accessions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_delta_checks_accession_id: %', SQLERRM;
END $$;

-- ===== lab_operation_result_releases =====
CREATE TABLE IF NOT EXISTS lab_operation_result_releases (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_operation_result_releases ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_operation_result_releases ADD COLUMN IF NOT EXISTS release_code VARCHAR(50);
ALTER TABLE lab_operation_result_releases ADD COLUMN IF NOT EXISTS accession_id VARCHAR(36);
ALTER TABLE lab_operation_result_releases ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE lab_operation_result_releases ADD COLUMN IF NOT EXISTS released_by VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE lab_operation_result_releases ADD COLUMN IF NOT EXISTS release_channel VARCHAR(50) DEFAULT 'PATIENT_PORTAL';
ALTER TABLE lab_operation_result_releases ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'RELEASED';
ALTER TABLE lab_operation_result_releases ADD COLUMN IF NOT EXISTS released_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_operation_result_releases ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_operation_result_releases_release_code ON lab_operation_result_releases (release_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_operation_result_releases_release_code'
  ) THEN
    ALTER TABLE lab_operation_result_releases
      ADD CONSTRAINT uq_lab_operation_result_releases_release_code UNIQUE (release_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.lab_results') IS NULL THEN
    RAISE NOTICE 'lab_results missing — skip FK fk_lab_operation_result_releases_lab_result_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_operation_result_releases_lab_result_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_operation_result_releases
    ADD CONSTRAINT fk_lab_operation_result_releases_lab_result_id
    FOREIGN KEY (lab_result_id) REFERENCES lab_results (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_operation_result_releases_lab_result_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.lab_sample_accessions') IS NULL THEN
    RAISE NOTICE 'lab_sample_accessions missing — skip FK fk_lab_operation_result_releases_accession_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_operation_result_releases_accession_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_operation_result_releases
    ADD CONSTRAINT fk_lab_operation_result_releases_accession_id
    FOREIGN KEY (accession_id) REFERENCES lab_sample_accessions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_operation_result_releases_accession_id: %', SQLERRM;
END $$;

-- ===== lab_pathologist_reviews =====
CREATE TABLE IF NOT EXISTS lab_pathologist_reviews (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_pathologist_reviews ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_pathologist_reviews ADD COLUMN IF NOT EXISTS review_code VARCHAR(50);
ALTER TABLE lab_pathologist_reviews ADD COLUMN IF NOT EXISTS accession_id VARCHAR(36);
ALTER TABLE lab_pathologist_reviews ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE lab_pathologist_reviews ADD COLUMN IF NOT EXISTS pathologist VARCHAR(255);
ALTER TABLE lab_pathologist_reviews ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE lab_pathologist_reviews ADD COLUMN IF NOT EXISTS diagnosis_notes TEXT;
ALTER TABLE lab_pathologist_reviews ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_pathologist_reviews ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_pathologist_reviews_review_code ON lab_pathologist_reviews (review_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_pathologist_reviews_review_code'
  ) THEN
    ALTER TABLE lab_pathologist_reviews
      ADD CONSTRAINT uq_lab_pathologist_reviews_review_code UNIQUE (review_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.lab_sample_accessions') IS NULL THEN
    RAISE NOTICE 'lab_sample_accessions missing — skip FK fk_lab_pathologist_reviews_accession_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_pathologist_reviews_accession_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_pathologist_reviews
    ADD CONSTRAINT fk_lab_pathologist_reviews_accession_id
    FOREIGN KEY (accession_id) REFERENCES lab_sample_accessions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_pathologist_reviews_accession_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.lab_results') IS NULL THEN
    RAISE NOTICE 'lab_results missing — skip FK fk_lab_pathologist_reviews_lab_result_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_pathologist_reviews_lab_result_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_pathologist_reviews
    ADD CONSTRAINT fk_lab_pathologist_reviews_lab_result_id
    FOREIGN KEY (lab_result_id) REFERENCES lab_results (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_pathologist_reviews_lab_result_id: %', SQLERRM;
END $$;

-- ===== lab_quality_controls =====
CREATE TABLE IF NOT EXISTS lab_quality_controls (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS qc_code VARCHAR(50);
ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS accession_id VARCHAR(36);
ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS analyzer_id VARCHAR(36);
ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS control_level VARCHAR(50) DEFAULT 'LEVEL_1';
ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS expected_value FLOAT;
ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS observed_value FLOAT;
ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(255);
ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS performed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_quality_controls ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_quality_controls_qc_code ON lab_quality_controls (qc_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_quality_controls_qc_code'
  ) THEN
    ALTER TABLE lab_quality_controls
      ADD CONSTRAINT uq_lab_quality_controls_qc_code UNIQUE (qc_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.lab_analyzers') IS NULL THEN
    RAISE NOTICE 'lab_analyzers missing — skip FK fk_lab_quality_controls_analyzer_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_quality_controls_analyzer_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_quality_controls
    ADD CONSTRAINT fk_lab_quality_controls_analyzer_id
    FOREIGN KEY (analyzer_id) REFERENCES lab_analyzers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_quality_controls_analyzer_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.lab_sample_accessions') IS NULL THEN
    RAISE NOTICE 'lab_sample_accessions missing — skip FK fk_lab_quality_controls_accession_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_quality_controls_accession_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_quality_controls
    ADD CONSTRAINT fk_lab_quality_controls_accession_id
    FOREIGN KEY (accession_id) REFERENCES lab_sample_accessions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_quality_controls_accession_id: %', SQLERRM;
END $$;

-- ===== lab_result_approvals =====
CREATE TABLE IF NOT EXISTS lab_result_approvals (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_result_approvals ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_result_approvals ADD COLUMN IF NOT EXISTS approval_code VARCHAR(50);
ALTER TABLE lab_result_approvals ADD COLUMN IF NOT EXISTS accession_id VARCHAR(36);
ALTER TABLE lab_result_approvals ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE lab_result_approvals ADD COLUMN IF NOT EXISTS approver VARCHAR(255);
ALTER TABLE lab_result_approvals ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE lab_result_approvals ADD COLUMN IF NOT EXISTS comments TEXT;
ALTER TABLE lab_result_approvals ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_result_approvals ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_result_approvals_approval_code ON lab_result_approvals (approval_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_result_approvals_approval_code'
  ) THEN
    ALTER TABLE lab_result_approvals
      ADD CONSTRAINT uq_lab_result_approvals_approval_code UNIQUE (approval_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.lab_results') IS NULL THEN
    RAISE NOTICE 'lab_results missing — skip FK fk_lab_result_approvals_lab_result_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_result_approvals_lab_result_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_result_approvals
    ADD CONSTRAINT fk_lab_result_approvals_lab_result_id
    FOREIGN KEY (lab_result_id) REFERENCES lab_results (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_result_approvals_lab_result_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.lab_sample_accessions') IS NULL THEN
    RAISE NOTICE 'lab_sample_accessions missing — skip FK fk_lab_result_approvals_accession_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_result_approvals_accession_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_result_approvals
    ADD CONSTRAINT fk_lab_result_approvals_accession_id
    FOREIGN KEY (accession_id) REFERENCES lab_sample_accessions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_result_approvals_accession_id: %', SQLERRM;
END $$;

-- ===== lab_result_items =====
CREATE TABLE IF NOT EXISTS lab_result_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_result_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_result_items ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE lab_result_items ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE lab_result_items ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE lab_result_items ADD COLUMN IF NOT EXISTS result_value VARCHAR(255);
ALTER TABLE lab_result_items ADD COLUMN IF NOT EXISTS unit VARCHAR(50);
ALTER TABLE lab_result_items ADD COLUMN IF NOT EXISTS reference_range VARCHAR(255);
ALTER TABLE lab_result_items ADD COLUMN IF NOT EXISTS flag VARCHAR(20) DEFAULT 'NORMAL';
ALTER TABLE lab_result_items ADD COLUMN IF NOT EXISTS sequence INTEGER DEFAULT 0;
ALTER TABLE lab_result_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.lab_results') IS NULL THEN
    RAISE NOTICE 'lab_results missing — skip FK fk_lab_result_items_lab_result_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_result_items_lab_result_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_result_items
    ADD CONSTRAINT fk_lab_result_items_lab_result_id
    FOREIGN KEY (lab_result_id) REFERENCES lab_results (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_result_items_lab_result_id: %', SQLERRM;
END $$;

-- ===== lab_results =====
CREATE TABLE IF NOT EXISTS lab_results (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS result_code VARCHAR(50);
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS patient_id VARCHAR(36);
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS patient_name VARCHAR(255);
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS source_type VARCHAR(50) DEFAULT 'MANUAL';
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS released_version INTEGER;
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS analyzer_payload_json TEXT;
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE;
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS released_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_results ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_results_result_code ON lab_results (result_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_results_result_code'
  ) THEN
    ALTER TABLE lab_results
      ADD CONSTRAINT uq_lab_results_result_code UNIQUE (result_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_lab_results_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_results_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_results
    ADD CONSTRAINT fk_lab_results_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_results_medical_order_id: %', SQLERRM;
END $$;

-- ===== lab_sample_accessions =====
CREATE TABLE IF NOT EXISTS lab_sample_accessions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS accession_code VARCHAR(50);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS sample_code VARCHAR(50);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS medical_sample_id VARCHAR(36);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS patient_name VARCHAR(255);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS sample_type VARCHAR(100);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS workflow_stage VARCHAR(50) DEFAULT 'BOOKING';
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS worklist_id VARCHAR(36);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS lab_bench_id VARCHAR(36);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS lab_shift_id VARCHAR(36);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS analyzer_id VARCHAR(36);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'NORMAL';
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS tat_target_minutes INTEGER DEFAULT 240;
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS received_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS released_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS assigned_technician VARCHAR(255);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS assigned_pathologist VARCHAR(255);
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_sample_accessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_sample_accessions_accession_code ON lab_sample_accessions (accession_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_sample_accessions_accession_code'
  ) THEN
    ALTER TABLE lab_sample_accessions
      ADD CONSTRAINT uq_lab_sample_accessions_accession_code UNIQUE (accession_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.lab_benches') IS NULL THEN
    RAISE NOTICE 'lab_benches missing — skip FK fk_lab_sample_accessions_lab_bench_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_sample_accessions_lab_bench_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_sample_accessions
    ADD CONSTRAINT fk_lab_sample_accessions_lab_bench_id
    FOREIGN KEY (lab_bench_id) REFERENCES lab_benches (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_sample_accessions_lab_bench_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.medical_samples') IS NULL THEN
    RAISE NOTICE 'medical_samples missing — skip FK fk_lab_sample_accessions_medical_sample_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_sample_accessions_medical_sample_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_sample_accessions
    ADD CONSTRAINT fk_lab_sample_accessions_medical_sample_id
    FOREIGN KEY (medical_sample_id) REFERENCES medical_samples (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_sample_accessions_medical_sample_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.lab_analyzers') IS NULL THEN
    RAISE NOTICE 'lab_analyzers missing — skip FK fk_lab_sample_accessions_analyzer_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_sample_accessions_analyzer_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_sample_accessions
    ADD CONSTRAINT fk_lab_sample_accessions_analyzer_id
    FOREIGN KEY (analyzer_id) REFERENCES lab_analyzers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_sample_accessions_analyzer_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_lab_sample_accessions_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_sample_accessions_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_sample_accessions
    ADD CONSTRAINT fk_lab_sample_accessions_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_sample_accessions_medical_order_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.lab_worklists') IS NULL THEN
    RAISE NOTICE 'lab_worklists missing — skip FK fk_lab_sample_accessions_worklist_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_sample_accessions_worklist_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_sample_accessions
    ADD CONSTRAINT fk_lab_sample_accessions_worklist_id
    FOREIGN KEY (worklist_id) REFERENCES lab_worklists (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_sample_accessions_worklist_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.lab_shifts') IS NULL THEN
    RAISE NOTICE 'lab_shifts missing — skip FK fk_lab_sample_accessions_lab_shift_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_sample_accessions_lab_shift_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_sample_accessions
    ADD CONSTRAINT fk_lab_sample_accessions_lab_shift_id
    FOREIGN KEY (lab_shift_id) REFERENCES lab_shifts (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_sample_accessions_lab_shift_id: %', SQLERRM;
END $$;

-- ===== lab_shifts =====
CREATE TABLE IF NOT EXISTS lab_shifts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_shifts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_shifts ADD COLUMN IF NOT EXISTS shift_code VARCHAR(50);
ALTER TABLE lab_shifts ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE lab_shifts ADD COLUMN IF NOT EXISTS start_time TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_shifts ADD COLUMN IF NOT EXISTS end_time TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_shifts ADD COLUMN IF NOT EXISTS supervisor VARCHAR(255);
ALTER TABLE lab_shifts ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE lab_shifts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_shifts_shift_code ON lab_shifts (shift_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_shifts_shift_code'
  ) THEN
    ALTER TABLE lab_shifts
      ADD CONSTRAINT uq_lab_shifts_shift_code UNIQUE (shift_code);
  END IF;
END $$;


-- ===== lab_technician_reviews =====
CREATE TABLE IF NOT EXISTS lab_technician_reviews (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_technician_reviews ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_technician_reviews ADD COLUMN IF NOT EXISTS review_code VARCHAR(50);
ALTER TABLE lab_technician_reviews ADD COLUMN IF NOT EXISTS accession_id VARCHAR(36);
ALTER TABLE lab_technician_reviews ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE lab_technician_reviews ADD COLUMN IF NOT EXISTS reviewer VARCHAR(255);
ALTER TABLE lab_technician_reviews ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE lab_technician_reviews ADD COLUMN IF NOT EXISTS comments TEXT;
ALTER TABLE lab_technician_reviews ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_technician_reviews ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_technician_reviews_review_code ON lab_technician_reviews (review_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_technician_reviews_review_code'
  ) THEN
    ALTER TABLE lab_technician_reviews
      ADD CONSTRAINT uq_lab_technician_reviews_review_code UNIQUE (review_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.lab_sample_accessions') IS NULL THEN
    RAISE NOTICE 'lab_sample_accessions missing — skip FK fk_lab_technician_reviews_accession_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_technician_reviews_accession_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_technician_reviews
    ADD CONSTRAINT fk_lab_technician_reviews_accession_id
    FOREIGN KEY (accession_id) REFERENCES lab_sample_accessions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_technician_reviews_accession_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.lab_results') IS NULL THEN
    RAISE NOTICE 'lab_results missing — skip FK fk_lab_technician_reviews_lab_result_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_technician_reviews_lab_result_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_technician_reviews
    ADD CONSTRAINT fk_lab_technician_reviews_lab_result_id
    FOREIGN KEY (lab_result_id) REFERENCES lab_results (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_technician_reviews_lab_result_id: %', SQLERRM;
END $$;

-- ===== lab_workflow_transitions =====
CREATE TABLE IF NOT EXISTS lab_workflow_transitions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_workflow_transitions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_workflow_transitions ADD COLUMN IF NOT EXISTS accession_id VARCHAR(36);
ALTER TABLE lab_workflow_transitions ADD COLUMN IF NOT EXISTS from_stage VARCHAR(50);
ALTER TABLE lab_workflow_transitions ADD COLUMN IF NOT EXISTS to_stage VARCHAR(50);
ALTER TABLE lab_workflow_transitions ADD COLUMN IF NOT EXISTS actor VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE lab_workflow_transitions ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE lab_workflow_transitions ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE lab_workflow_transitions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.lab_sample_accessions') IS NULL THEN
    RAISE NOTICE 'lab_sample_accessions missing — skip FK fk_lab_workflow_transitions_accession_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_workflow_transitions_accession_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_workflow_transitions
    ADD CONSTRAINT fk_lab_workflow_transitions_accession_id
    FOREIGN KEY (accession_id) REFERENCES lab_sample_accessions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_workflow_transitions_accession_id: %', SQLERRM;
END $$;

-- ===== lab_worklists =====
CREATE TABLE IF NOT EXISTS lab_worklists (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lab_worklists ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lab_worklists ADD COLUMN IF NOT EXISTS worklist_code VARCHAR(50);
ALTER TABLE lab_worklists ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE lab_worklists ADD COLUMN IF NOT EXISTS lab_bench_id VARCHAR(36);
ALTER TABLE lab_worklists ADD COLUMN IF NOT EXISTS lab_shift_id VARCHAR(36);
ALTER TABLE lab_worklists ADD COLUMN IF NOT EXISTS assigned_technician VARCHAR(255);
ALTER TABLE lab_worklists ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'OPEN';
ALTER TABLE lab_worklists ADD COLUMN IF NOT EXISTS sample_count INTEGER DEFAULT 0;
ALTER TABLE lab_worklists ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lab_worklists ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lab_worklists_worklist_code ON lab_worklists (worklist_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_lab_worklists_worklist_code'
  ) THEN
    ALTER TABLE lab_worklists
      ADD CONSTRAINT uq_lab_worklists_worklist_code UNIQUE (worklist_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.lab_benches') IS NULL THEN
    RAISE NOTICE 'lab_benches missing — skip FK fk_lab_worklists_lab_bench_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_worklists_lab_bench_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_worklists
    ADD CONSTRAINT fk_lab_worklists_lab_bench_id
    FOREIGN KEY (lab_bench_id) REFERENCES lab_benches (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_worklists_lab_bench_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.lab_shifts') IS NULL THEN
    RAISE NOTICE 'lab_shifts missing — skip FK fk_lab_worklists_lab_shift_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lab_worklists_lab_shift_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lab_worklists
    ADD CONSTRAINT fk_lab_worklists_lab_shift_id
    FOREIGN KEY (lab_shift_id) REFERENCES lab_shifts (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lab_worklists_lab_shift_id: %', SQLERRM;
END $$;

-- ===== laboratories =====
CREATE TABLE IF NOT EXISTS laboratories (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE laboratories ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE laboratories ADD COLUMN IF NOT EXISTS code VARCHAR(50);
ALTER TABLE laboratories ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE laboratories ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE laboratories ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
ALTER TABLE laboratories ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE laboratories ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE laboratories ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE laboratories ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE laboratories ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_laboratories_code ON laboratories (code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_laboratories_code'
  ) THEN
    ALTER TABLE laboratories
      ADD CONSTRAINT uq_laboratories_code UNIQUE (code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.enterprise_tenants') IS NULL THEN
    RAISE NOTICE 'enterprise_tenants missing — skip FK fk_laboratories_tenant_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_laboratories_tenant_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE laboratories
    ADD CONSTRAINT fk_laboratories_tenant_id
    FOREIGN KEY (tenant_id) REFERENCES enterprise_tenants (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_laboratories_tenant_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.enterprise_organizations') IS NULL THEN
    RAISE NOTICE 'enterprise_organizations missing — skip FK fk_laboratories_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_laboratories_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE laboratories
    ADD CONSTRAINT fk_laboratories_organization_id
    FOREIGN KEY (organization_id) REFERENCES enterprise_organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_laboratories_organization_id: %', SQLERRM;
END $$;

-- ===== launch_checklist_items =====
CREATE TABLE IF NOT EXISTS launch_checklist_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE launch_checklist_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE launch_checklist_items ADD COLUMN IF NOT EXISTS category VARCHAR(50);
ALTER TABLE launch_checklist_items ADD COLUMN IF NOT EXISTS item_key VARCHAR(100);
ALTER TABLE launch_checklist_items ADD COLUMN IF NOT EXISTS label VARCHAR(255);
ALTER TABLE launch_checklist_items ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'pending';
ALTER TABLE launch_checklist_items ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE launch_checklist_items ADD COLUMN IF NOT EXISTS verified_by VARCHAR(255);
ALTER TABLE launch_checklist_items ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE launch_checklist_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE launch_checklist_items ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_launch_checklist_items_item_key ON launch_checklist_items (item_key);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_launch_checklist_items_item_key'
  ) THEN
    ALTER TABLE launch_checklist_items
      ADD CONSTRAINT uq_launch_checklist_items_item_key UNIQUE (item_key);
  END IF;
END $$;


-- ===== lis_connectors =====
CREATE TABLE IF NOT EXISTS lis_connectors (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS connector_code VARCHAR(50);
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS connector_name VARCHAR(255);
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS connector_type VARCHAR(30) DEFAULT 'MANUAL';
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS laboratory_id VARCHAR(36);
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS base_url VARCHAR(500);
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS auth_type VARCHAR(30);
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS username VARCHAR(255);
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS api_key_reference VARCHAR(255);
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS sftp_host VARCHAR(255);
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS sftp_path VARCHAR(500);
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'active';
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS last_sync_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lis_connectors ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lis_connectors_connector_code ON lis_connectors (connector_code);



-- ===== lis_field_mappings =====
CREATE TABLE IF NOT EXISTS lis_field_mappings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lis_field_mappings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lis_field_mappings ADD COLUMN IF NOT EXISTS connector_id VARCHAR(36);
ALTER TABLE lis_field_mappings ADD COLUMN IF NOT EXISTS external_field VARCHAR(100);
ALTER TABLE lis_field_mappings ADD COLUMN IF NOT EXISTS dxcon_field VARCHAR(100);
ALTER TABLE lis_field_mappings ADD COLUMN IF NOT EXISTS transform_rule VARCHAR(255);
ALTER TABLE lis_field_mappings ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE lis_field_mappings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_lis_field_mappings_connector_id ON lis_field_mappings (connector_id);


DO $$
BEGIN
  IF to_regclass('public.lis_connectors') IS NULL THEN
    RAISE NOTICE 'lis_connectors missing — skip FK fk_lis_field_mappings_connector_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lis_field_mappings_connector_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lis_field_mappings
    ADD CONSTRAINT fk_lis_field_mappings_connector_id
    FOREIGN KEY (connector_id) REFERENCES lis_connectors (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lis_field_mappings_connector_id: %', SQLERRM;
END $$;

-- ===== lis_import_batches =====
CREATE TABLE IF NOT EXISTS lis_import_batches (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lis_import_batches ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lis_import_batches ADD COLUMN IF NOT EXISTS batch_code VARCHAR(50);
ALTER TABLE lis_import_batches ADD COLUMN IF NOT EXISTS connector_id VARCHAR(36);
ALTER TABLE lis_import_batches ADD COLUMN IF NOT EXISTS import_type VARCHAR(30);
ALTER TABLE lis_import_batches ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);
ALTER TABLE lis_import_batches ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'processing';
ALTER TABLE lis_import_batches ADD COLUMN IF NOT EXISTS total_rows INTEGER DEFAULT 0;
ALTER TABLE lis_import_batches ADD COLUMN IF NOT EXISTS success_rows INTEGER DEFAULT 0;
ALTER TABLE lis_import_batches ADD COLUMN IF NOT EXISTS failed_rows INTEGER DEFAULT 0;
ALTER TABLE lis_import_batches ADD COLUMN IF NOT EXISTS imported_by VARCHAR(255);
ALTER TABLE lis_import_batches ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_lis_import_batches_batch_code ON lis_import_batches (batch_code);


DO $$
BEGIN
  IF to_regclass('public.lis_connectors') IS NULL THEN
    RAISE NOTICE 'lis_connectors missing — skip FK fk_lis_import_batches_connector_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lis_import_batches_connector_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lis_import_batches
    ADD CONSTRAINT fk_lis_import_batches_connector_id
    FOREIGN KEY (connector_id) REFERENCES lis_connectors (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lis_import_batches_connector_id: %', SQLERRM;
END $$;

-- ===== lis_import_failed_rows =====
CREATE TABLE IF NOT EXISTS lis_import_failed_rows (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lis_import_failed_rows ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lis_import_failed_rows ADD COLUMN IF NOT EXISTS batch_id VARCHAR(36);
ALTER TABLE lis_import_failed_rows ADD COLUMN IF NOT EXISTS connector_id VARCHAR(36);
ALTER TABLE lis_import_failed_rows ADD COLUMN IF NOT EXISTS row_number INTEGER;
ALTER TABLE lis_import_failed_rows ADD COLUMN IF NOT EXISTS error_reason TEXT;
ALTER TABLE lis_import_failed_rows ADD COLUMN IF NOT EXISTS raw_payload TEXT;
ALTER TABLE lis_import_failed_rows ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'failed';
ALTER TABLE lis_import_failed_rows ADD COLUMN IF NOT EXISTS retried_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lis_import_failed_rows ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_lis_import_failed_rows_batch_id ON lis_import_failed_rows (batch_id);


DO $$
BEGIN
  IF to_regclass('public.lis_import_batches') IS NULL THEN
    RAISE NOTICE 'lis_import_batches missing — skip FK fk_lis_import_failed_rows_batch_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lis_import_failed_rows_batch_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lis_import_failed_rows
    ADD CONSTRAINT fk_lis_import_failed_rows_batch_id
    FOREIGN KEY (batch_id) REFERENCES lis_import_batches (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lis_import_failed_rows_batch_id: %', SQLERRM;
END $$;

-- ===== lis_order_messages =====
CREATE TABLE IF NOT EXISTS lis_order_messages (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lis_order_messages ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lis_order_messages ADD COLUMN IF NOT EXISTS message_id VARCHAR(36);
ALTER TABLE lis_order_messages ADD COLUMN IF NOT EXISTS external_order_id VARCHAR(100);
ALTER TABLE lis_order_messages ADD COLUMN IF NOT EXISTS patient_code VARCHAR(100);
ALTER TABLE lis_order_messages ADD COLUMN IF NOT EXISTS test_codes_json TEXT DEFAULT '[]';
ALTER TABLE lis_order_messages ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE lis_order_messages ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.integration_messages') IS NULL THEN
    RAISE NOTICE 'integration_messages missing — skip FK fk_lis_order_messages_message_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lis_order_messages_message_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lis_order_messages
    ADD CONSTRAINT fk_lis_order_messages_message_id
    FOREIGN KEY (message_id) REFERENCES integration_messages (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lis_order_messages_message_id: %', SQLERRM;
END $$;

-- ===== lis_result_messages =====
CREATE TABLE IF NOT EXISTS lis_result_messages (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE lis_result_messages ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE lis_result_messages ADD COLUMN IF NOT EXISTS message_id VARCHAR(36);
ALTER TABLE lis_result_messages ADD COLUMN IF NOT EXISTS external_order_id VARCHAR(100);
ALTER TABLE lis_result_messages ADD COLUMN IF NOT EXISTS result_code VARCHAR(100);
ALTER TABLE lis_result_messages ADD COLUMN IF NOT EXISTS result_value VARCHAR(255);
ALTER TABLE lis_result_messages ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE lis_result_messages ADD COLUMN IF NOT EXISTS released_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE lis_result_messages ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.integration_messages') IS NULL THEN
    RAISE NOTICE 'integration_messages missing — skip FK fk_lis_result_messages_message_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_lis_result_messages_message_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE lis_result_messages
    ADD CONSTRAINT fk_lis_result_messages_message_id
    FOREIGN KEY (message_id) REFERENCES integration_messages (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_lis_result_messages_message_id: %', SQLERRM;
END $$;

-- ===== logistics_chain_of_custody_events =====
CREATE TABLE IF NOT EXISTS logistics_chain_of_custody_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE logistics_chain_of_custody_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE logistics_chain_of_custody_events ADD COLUMN IF NOT EXISTS event_code VARCHAR(50);
ALTER TABLE logistics_chain_of_custody_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(50);
ALTER TABLE logistics_chain_of_custody_events ADD COLUMN IF NOT EXISTS reference_type VARCHAR(50);
ALTER TABLE logistics_chain_of_custody_events ADD COLUMN IF NOT EXISTS reference_id VARCHAR(36);
ALTER TABLE logistics_chain_of_custody_events ADD COLUMN IF NOT EXISTS actor VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE logistics_chain_of_custody_events ADD COLUMN IF NOT EXISTS location VARCHAR(255);
ALTER TABLE logistics_chain_of_custody_events ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE logistics_chain_of_custody_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_logistics_chain_of_custody_events_event_code ON logistics_chain_of_custody_events (event_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_logistics_chain_of_custody_events_event_code'
  ) THEN
    ALTER TABLE logistics_chain_of_custody_events
      ADD CONSTRAINT uq_logistics_chain_of_custody_events_event_code UNIQUE (event_code);
  END IF;
END $$;


-- ===== logistics_delivery_proofs =====
CREATE TABLE IF NOT EXISTS logistics_delivery_proofs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE logistics_delivery_proofs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE logistics_delivery_proofs ADD COLUMN IF NOT EXISTS assignment_id VARCHAR(36);
ALTER TABLE logistics_delivery_proofs ADD COLUMN IF NOT EXISTS route_stop_id VARCHAR(36);
ALTER TABLE logistics_delivery_proofs ADD COLUMN IF NOT EXISTS proof_type VARCHAR(50) DEFAULT 'SIGNATURE';
ALTER TABLE logistics_delivery_proofs ADD COLUMN IF NOT EXISTS proof_url VARCHAR(500);
ALTER TABLE logistics_delivery_proofs ADD COLUMN IF NOT EXISTS recipient_name VARCHAR(255);
ALTER TABLE logistics_delivery_proofs ADD COLUMN IF NOT EXISTS captured_by VARCHAR(255);
ALTER TABLE logistics_delivery_proofs ADD COLUMN IF NOT EXISTS captured_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE logistics_delivery_proofs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.logistics_route_stops') IS NULL THEN
    RAISE NOTICE 'logistics_route_stops missing — skip FK fk_logistics_delivery_proofs_route_stop_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_delivery_proofs_route_stop_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_delivery_proofs
    ADD CONSTRAINT fk_logistics_delivery_proofs_route_stop_id
    FOREIGN KEY (route_stop_id) REFERENCES logistics_route_stops (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_delivery_proofs_route_stop_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.logistics_dispatch_assignments') IS NULL THEN
    RAISE NOTICE 'logistics_dispatch_assignments missing — skip FK fk_logistics_delivery_proofs_assignment_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_delivery_proofs_assignment_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_delivery_proofs
    ADD CONSTRAINT fk_logistics_delivery_proofs_assignment_id
    FOREIGN KEY (assignment_id) REFERENCES logistics_dispatch_assignments (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_delivery_proofs_assignment_id: %', SQLERRM;
END $$;

-- ===== logistics_dispatch_assignments =====
CREATE TABLE IF NOT EXISTS logistics_dispatch_assignments (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE logistics_dispatch_assignments ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE logistics_dispatch_assignments ADD COLUMN IF NOT EXISTS assignment_code VARCHAR(50);
ALTER TABLE logistics_dispatch_assignments ADD COLUMN IF NOT EXISTS driver_profile_id VARCHAR(36);
ALTER TABLE logistics_dispatch_assignments ADD COLUMN IF NOT EXISTS vehicle_id VARCHAR(36);
ALTER TABLE logistics_dispatch_assignments ADD COLUMN IF NOT EXISTS route_plan_id VARCHAR(36);
ALTER TABLE logistics_dispatch_assignments ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE logistics_dispatch_assignments ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'NORMAL';
ALTER TABLE logistics_dispatch_assignments ADD COLUMN IF NOT EXISTS reference_type VARCHAR(50);
ALTER TABLE logistics_dispatch_assignments ADD COLUMN IF NOT EXISTS reference_id VARCHAR(36);
ALTER TABLE logistics_dispatch_assignments ADD COLUMN IF NOT EXISTS assigned_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE logistics_dispatch_assignments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_logistics_dispatch_assignments_assignment_code ON logistics_dispatch_assignments (assignment_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_logistics_dispatch_assignments_assignment_code'
  ) THEN
    ALTER TABLE logistics_dispatch_assignments
      ADD CONSTRAINT uq_logistics_dispatch_assignments_assignment_code UNIQUE (assignment_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.logistics_route_plans') IS NULL THEN
    RAISE NOTICE 'logistics_route_plans missing — skip FK fk_logistics_dispatch_assignments_route_plan_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_dispatch_assignments_route_plan_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_dispatch_assignments
    ADD CONSTRAINT fk_logistics_dispatch_assignments_route_plan_id
    FOREIGN KEY (route_plan_id) REFERENCES logistics_route_plans (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_dispatch_assignments_route_plan_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.logistics_driver_profiles') IS NULL THEN
    RAISE NOTICE 'logistics_driver_profiles missing — skip FK fk_logistics_dispatch_assignments_driver_profile_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_dispatch_assignments_driver_profile_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_dispatch_assignments
    ADD CONSTRAINT fk_logistics_dispatch_assignments_driver_profile_id
    FOREIGN KEY (driver_profile_id) REFERENCES logistics_driver_profiles (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_dispatch_assignments_driver_profile_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.logistics_vehicles') IS NULL THEN
    RAISE NOTICE 'logistics_vehicles missing — skip FK fk_logistics_dispatch_assignments_vehicle_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_dispatch_assignments_vehicle_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_dispatch_assignments
    ADD CONSTRAINT fk_logistics_dispatch_assignments_vehicle_id
    FOREIGN KEY (vehicle_id) REFERENCES logistics_vehicles (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_dispatch_assignments_vehicle_id: %', SQLERRM;
END $$;

-- ===== logistics_driver_profiles =====
CREATE TABLE IF NOT EXISTS logistics_driver_profiles (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS profile_code VARCHAR(50);
ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS driver_id VARCHAR(36);
ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS license_number VARCHAR(100);
ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS hub_city VARCHAR(100);
ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS rating FLOAT DEFAULT 5.0;
ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS active_vehicle_id VARCHAR(36);
ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE logistics_driver_profiles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_logistics_driver_profiles_profile_code ON logistics_driver_profiles (profile_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_logistics_driver_profiles_profile_code'
  ) THEN
    ALTER TABLE logistics_driver_profiles
      ADD CONSTRAINT uq_logistics_driver_profiles_profile_code UNIQUE (profile_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.drivers') IS NULL THEN
    RAISE NOTICE 'drivers missing — skip FK fk_logistics_driver_profiles_driver_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_driver_profiles_driver_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_driver_profiles
    ADD CONSTRAINT fk_logistics_driver_profiles_driver_id
    FOREIGN KEY (driver_id) REFERENCES drivers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_driver_profiles_driver_id: %', SQLERRM;
END $$;

-- ===== logistics_eta_estimates =====
CREATE TABLE IF NOT EXISTS logistics_eta_estimates (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE logistics_eta_estimates ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE logistics_eta_estimates ADD COLUMN IF NOT EXISTS route_plan_id VARCHAR(36);
ALTER TABLE logistics_eta_estimates ADD COLUMN IF NOT EXISTS route_stop_id VARCHAR(36);
ALTER TABLE logistics_eta_estimates ADD COLUMN IF NOT EXISTS estimated_arrival TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE logistics_eta_estimates ADD COLUMN IF NOT EXISTS estimated_minutes INTEGER DEFAULT 0;
ALTER TABLE logistics_eta_estimates ADD COLUMN IF NOT EXISTS confidence FLOAT DEFAULT 0.9;
ALTER TABLE logistics_eta_estimates ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.logistics_route_stops') IS NULL THEN
    RAISE NOTICE 'logistics_route_stops missing — skip FK fk_logistics_eta_estimates_route_stop_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_eta_estimates_route_stop_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_eta_estimates
    ADD CONSTRAINT fk_logistics_eta_estimates_route_stop_id
    FOREIGN KEY (route_stop_id) REFERENCES logistics_route_stops (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_eta_estimates_route_stop_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.logistics_route_plans') IS NULL THEN
    RAISE NOTICE 'logistics_route_plans missing — skip FK fk_logistics_eta_estimates_route_plan_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_eta_estimates_route_plan_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_eta_estimates
    ADD CONSTRAINT fk_logistics_eta_estimates_route_plan_id
    FOREIGN KEY (route_plan_id) REFERENCES logistics_route_plans (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_eta_estimates_route_plan_id: %', SQLERRM;
END $$;

-- ===== logistics_gps_pings =====
CREATE TABLE IF NOT EXISTS logistics_gps_pings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE logistics_gps_pings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE logistics_gps_pings ADD COLUMN IF NOT EXISTS driver_profile_id VARCHAR(36);
ALTER TABLE logistics_gps_pings ADD COLUMN IF NOT EXISTS vehicle_id VARCHAR(36);
ALTER TABLE logistics_gps_pings ADD COLUMN IF NOT EXISTS route_plan_id VARCHAR(36);
ALTER TABLE logistics_gps_pings ADD COLUMN IF NOT EXISTS latitude FLOAT;
ALTER TABLE logistics_gps_pings ADD COLUMN IF NOT EXISTS longitude FLOAT;
ALTER TABLE logistics_gps_pings ADD COLUMN IF NOT EXISTS speed FLOAT DEFAULT 0;
ALTER TABLE logistics_gps_pings ADD COLUMN IF NOT EXISTS heading FLOAT DEFAULT 0;
ALTER TABLE logistics_gps_pings ADD COLUMN IF NOT EXISTS recorded_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE logistics_gps_pings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.logistics_driver_profiles') IS NULL THEN
    RAISE NOTICE 'logistics_driver_profiles missing — skip FK fk_logistics_gps_pings_driver_profile_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_gps_pings_driver_profile_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_gps_pings
    ADD CONSTRAINT fk_logistics_gps_pings_driver_profile_id
    FOREIGN KEY (driver_profile_id) REFERENCES logistics_driver_profiles (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_gps_pings_driver_profile_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.logistics_route_plans') IS NULL THEN
    RAISE NOTICE 'logistics_route_plans missing — skip FK fk_logistics_gps_pings_route_plan_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_gps_pings_route_plan_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_gps_pings
    ADD CONSTRAINT fk_logistics_gps_pings_route_plan_id
    FOREIGN KEY (route_plan_id) REFERENCES logistics_route_plans (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_gps_pings_route_plan_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.logistics_vehicles') IS NULL THEN
    RAISE NOTICE 'logistics_vehicles missing — skip FK fk_logistics_gps_pings_vehicle_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_gps_pings_vehicle_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_gps_pings
    ADD CONSTRAINT fk_logistics_gps_pings_vehicle_id
    FOREIGN KEY (vehicle_id) REFERENCES logistics_vehicles (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_gps_pings_vehicle_id: %', SQLERRM;
END $$;

-- ===== logistics_route_plans =====
CREATE TABLE IF NOT EXISTS logistics_route_plans (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS route_code VARCHAR(50);
ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS driver_profile_id VARCHAR(36);
ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS vehicle_id VARCHAR(36);
ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS total_stops INTEGER DEFAULT 0;
ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS total_distance_km FLOAT DEFAULT 0;
ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS estimated_minutes INTEGER DEFAULT 0;
ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS start_latitude FLOAT;
ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS start_longitude FLOAT;
ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS optimized_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE logistics_route_plans ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_logistics_route_plans_route_code ON logistics_route_plans (route_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_logistics_route_plans_route_code'
  ) THEN
    ALTER TABLE logistics_route_plans
      ADD CONSTRAINT uq_logistics_route_plans_route_code UNIQUE (route_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.logistics_vehicles') IS NULL THEN
    RAISE NOTICE 'logistics_vehicles missing — skip FK fk_logistics_route_plans_vehicle_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_route_plans_vehicle_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_route_plans
    ADD CONSTRAINT fk_logistics_route_plans_vehicle_id
    FOREIGN KEY (vehicle_id) REFERENCES logistics_vehicles (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_route_plans_vehicle_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.logistics_driver_profiles') IS NULL THEN
    RAISE NOTICE 'logistics_driver_profiles missing — skip FK fk_logistics_route_plans_driver_profile_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_route_plans_driver_profile_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_route_plans
    ADD CONSTRAINT fk_logistics_route_plans_driver_profile_id
    FOREIGN KEY (driver_profile_id) REFERENCES logistics_driver_profiles (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_route_plans_driver_profile_id: %', SQLERRM;
END $$;

-- ===== logistics_route_stops =====
CREATE TABLE IF NOT EXISTS logistics_route_stops (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE logistics_route_stops ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE logistics_route_stops ADD COLUMN IF NOT EXISTS route_plan_id VARCHAR(36);
ALTER TABLE logistics_route_stops ADD COLUMN IF NOT EXISTS stop_sequence INTEGER DEFAULT 0;
ALTER TABLE logistics_route_stops ADD COLUMN IF NOT EXISTS address VARCHAR(500);
ALTER TABLE logistics_route_stops ADD COLUMN IF NOT EXISTS latitude FLOAT;
ALTER TABLE logistics_route_stops ADD COLUMN IF NOT EXISTS longitude FLOAT;
ALTER TABLE logistics_route_stops ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE logistics_route_stops ADD COLUMN IF NOT EXISTS reference_type VARCHAR(50);
ALTER TABLE logistics_route_stops ADD COLUMN IF NOT EXISTS reference_id VARCHAR(36);
ALTER TABLE logistics_route_stops ADD COLUMN IF NOT EXISTS eta_minutes INTEGER DEFAULT 0;
ALTER TABLE logistics_route_stops ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.logistics_route_plans') IS NULL THEN
    RAISE NOTICE 'logistics_route_plans missing — skip FK fk_logistics_route_stops_route_plan_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_route_stops_route_plan_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_route_stops
    ADD CONSTRAINT fk_logistics_route_stops_route_plan_id
    FOREIGN KEY (route_plan_id) REFERENCES logistics_route_plans (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_route_stops_route_plan_id: %', SQLERRM;
END $$;

-- ===== logistics_vehicles =====
CREATE TABLE IF NOT EXISTS logistics_vehicles (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE logistics_vehicles ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE logistics_vehicles ADD COLUMN IF NOT EXISTS vehicle_code VARCHAR(50);
ALTER TABLE logistics_vehicles ADD COLUMN IF NOT EXISTS plate_number VARCHAR(50);
ALTER TABLE logistics_vehicles ADD COLUMN IF NOT EXISTS vehicle_type VARCHAR(50) DEFAULT 'VAN';
ALTER TABLE logistics_vehicles ADD COLUMN IF NOT EXISTS capacity INTEGER DEFAULT 20;
ALTER TABLE logistics_vehicles ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'AVAILABLE';
ALTER TABLE logistics_vehicles ADD COLUMN IF NOT EXISTS current_driver_profile_id VARCHAR(36);
ALTER TABLE logistics_vehicles ADD COLUMN IF NOT EXISTS latitude FLOAT;
ALTER TABLE logistics_vehicles ADD COLUMN IF NOT EXISTS longitude FLOAT;
ALTER TABLE logistics_vehicles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE logistics_vehicles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_logistics_vehicles_vehicle_code ON logistics_vehicles (vehicle_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_logistics_vehicles_vehicle_code'
  ) THEN
    ALTER TABLE logistics_vehicles
      ADD CONSTRAINT uq_logistics_vehicles_vehicle_code UNIQUE (vehicle_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.logistics_driver_profiles') IS NULL THEN
    RAISE NOTICE 'logistics_driver_profiles missing — skip FK fk_logistics_vehicles_current_driver_profile_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_logistics_vehicles_current_driver_profile_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE logistics_vehicles
    ADD CONSTRAINT fk_logistics_vehicles_current_driver_profile_id
    FOREIGN KEY (current_driver_profile_id) REFERENCES logistics_driver_profiles (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_logistics_vehicles_current_driver_profile_id: %', SQLERRM;
END $$;

-- ===== marketplace_booking_timelines =====
CREATE TABLE IF NOT EXISTS marketplace_booking_timelines (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE marketplace_booking_timelines ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE marketplace_booking_timelines ADD COLUMN IF NOT EXISTS booking_id VARCHAR(36);
ALTER TABLE marketplace_booking_timelines ADD COLUMN IF NOT EXISTS event_type VARCHAR(50);
ALTER TABLE marketplace_booking_timelines ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE marketplace_booking_timelines ADD COLUMN IF NOT EXISTS actor_email VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE marketplace_booking_timelines ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.marketplace_bookings') IS NULL THEN
    RAISE NOTICE 'marketplace_bookings missing — skip FK fk_marketplace_booking_timelines_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_marketplace_booking_timelines_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE marketplace_booking_timelines
    ADD CONSTRAINT fk_marketplace_booking_timelines_booking_id
    FOREIGN KEY (booking_id) REFERENCES marketplace_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_marketplace_booking_timelines_booking_id: %', SQLERRM;
END $$;

-- ===== marketplace_bookings =====
CREATE TABLE IF NOT EXISTS marketplace_bookings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS booking_code VARCHAR(50);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS patient_name VARCHAR(255);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS patient_phone VARCHAR(30);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS patient_email VARCHAR(255);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS patient_address TEXT;
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS province VARCHAR(100);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS city VARCHAR(100);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS district VARCHAR(100);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS diagnostic_service_id VARCHAR(36);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS partner_service_mapping_id VARCHAR(36);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS requested_date VARCHAR(20);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS requested_time_slot VARCHAR(50);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS scheduled_slot_id VARCHAR(36);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'CREATED';
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE marketplace_bookings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_marketplace_bookings_booking_code ON marketplace_bookings (booking_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_marketplace_bookings_booking_code'
  ) THEN
    ALTER TABLE marketplace_bookings
      ADD CONSTRAINT uq_marketplace_bookings_booking_code UNIQUE (booking_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.partner_service_mappings') IS NULL THEN
    RAISE NOTICE 'partner_service_mappings missing — skip FK fk_marketplace_bookings_partner_service_mapping_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_marketplace_bookings_partner_service_mapping_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE marketplace_bookings
    ADD CONSTRAINT fk_marketplace_bookings_partner_service_mapping_id
    FOREIGN KEY (partner_service_mapping_id) REFERENCES partner_service_mappings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_marketplace_bookings_partner_service_mapping_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.diagnostic_services') IS NULL THEN
    RAISE NOTICE 'diagnostic_services missing — skip FK fk_marketplace_bookings_diagnostic_service_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_marketplace_bookings_diagnostic_service_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE marketplace_bookings
    ADD CONSTRAINT fk_marketplace_bookings_diagnostic_service_id
    FOREIGN KEY (diagnostic_service_id) REFERENCES diagnostic_services (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_marketplace_bookings_diagnostic_service_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.scheduling_slots') IS NULL THEN
    RAISE NOTICE 'scheduling_slots missing — skip FK fk_marketplace_bookings_scheduled_slot_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_marketplace_bookings_scheduled_slot_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE marketplace_bookings
    ADD CONSTRAINT fk_marketplace_bookings_scheduled_slot_id
    FOREIGN KEY (scheduled_slot_id) REFERENCES scheduling_slots (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_marketplace_bookings_scheduled_slot_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_marketplace_bookings_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_marketplace_bookings_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE marketplace_bookings
    ADD CONSTRAINT fk_marketplace_bookings_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_marketplace_bookings_partner_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.orders') IS NULL THEN
    RAISE NOTICE 'orders missing — skip FK fk_marketplace_bookings_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_marketplace_bookings_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE marketplace_bookings
    ADD CONSTRAINT fk_marketplace_bookings_order_id
    FOREIGN KEY (order_id) REFERENCES orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_marketplace_bookings_order_id: %', SQLERRM;
END $$;

-- ===== mdm_import_batches =====
CREATE TABLE IF NOT EXISTS mdm_import_batches (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS batch_code VARCHAR(50);
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS entity_type VARCHAR(50);
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS file_format VARCHAR(20);
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS total_rows INTEGER DEFAULT 0;
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS valid_rows INTEGER DEFAULT 0;
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS duplicate_rows INTEGER DEFAULT 0;
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS error_rows INTEGER DEFAULT 0;
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS committed_rows INTEGER DEFAULT 0;
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'pending';
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS preview_json TEXT DEFAULT '{}';
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS error_summary TEXT;
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS approved_by VARCHAR(255);
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS committed_by VARCHAR(255);
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS committed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS rolled_back_by VARCHAR(255);
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS rolled_back_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS created_by VARCHAR(255);
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mdm_import_batches ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_mdm_import_batches_batch_code ON mdm_import_batches (batch_code);
CREATE INDEX IF NOT EXISTS ix_mdm_import_batches_entity_type ON mdm_import_batches (entity_type);
CREATE INDEX IF NOT EXISTS ix_mdm_import_batches_status ON mdm_import_batches (status);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mdm_import_batches_batch_code'
  ) THEN
    ALTER TABLE mdm_import_batches
      ADD CONSTRAINT uq_mdm_import_batches_batch_code UNIQUE (batch_code);
  END IF;
END $$;


-- ===== mdm_import_rows =====
CREATE TABLE IF NOT EXISTS mdm_import_rows (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mdm_import_rows ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mdm_import_rows ADD COLUMN IF NOT EXISTS batch_id VARCHAR(36);
ALTER TABLE mdm_import_rows ADD COLUMN IF NOT EXISTS row_number INTEGER;
ALTER TABLE mdm_import_rows ADD COLUMN IF NOT EXISTS code VARCHAR(100);
ALTER TABLE mdm_import_rows ADD COLUMN IF NOT EXISTS name VARCHAR(500);
ALTER TABLE mdm_import_rows ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'valid';
ALTER TABLE mdm_import_rows ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE mdm_import_rows ADD COLUMN IF NOT EXISTS validation_errors TEXT;
ALTER TABLE mdm_import_rows ADD COLUMN IF NOT EXISTS master_record_id VARCHAR(36);
ALTER TABLE mdm_import_rows ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_mdm_import_rows_batch_id ON mdm_import_rows (batch_id);


DO $$
BEGIN
  IF to_regclass('public.mdm_master_records') IS NULL THEN
    RAISE NOTICE 'mdm_master_records missing — skip FK fk_mdm_import_rows_master_record_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mdm_import_rows_master_record_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mdm_import_rows
    ADD CONSTRAINT fk_mdm_import_rows_master_record_id
    FOREIGN KEY (master_record_id) REFERENCES mdm_master_records (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mdm_import_rows_master_record_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.mdm_import_batches') IS NULL THEN
    RAISE NOTICE 'mdm_import_batches missing — skip FK fk_mdm_import_rows_batch_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mdm_import_rows_batch_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mdm_import_rows
    ADD CONSTRAINT fk_mdm_import_rows_batch_id
    FOREIGN KEY (batch_id) REFERENCES mdm_import_batches (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mdm_import_rows_batch_id: %', SQLERRM;
END $$;

-- ===== mdm_master_records =====
CREATE TABLE IF NOT EXISTS mdm_master_records (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS entity_type VARCHAR(50);
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS code VARCHAR(100);
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS name VARCHAR(500);
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS attributes_json TEXT DEFAULT '{}';
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS parent_code VARCHAR(100);
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'mdm';
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS external_id VARCHAR(100);
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS import_batch_id VARCHAR(36);
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS created_by VARCHAR(255);
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255);
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mdm_master_records ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_mdm_master_records_entity_type ON mdm_master_records (entity_type);
CREATE INDEX IF NOT EXISTS ix_mdm_master_records_code ON mdm_master_records (code);
CREATE INDEX IF NOT EXISTS ix_mdm_master_records_status ON mdm_master_records (status);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mdm_entity_code'
  ) THEN
    ALTER TABLE mdm_master_records
      ADD CONSTRAINT uq_mdm_entity_code UNIQUE (entity_type, code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.mdm_import_batches') IS NULL THEN
    RAISE NOTICE 'mdm_import_batches missing — skip FK fk_mdm_master_records_import_batch_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mdm_master_records_import_batch_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mdm_master_records
    ADD CONSTRAINT fk_mdm_master_records_import_batch_id
    FOREIGN KEY (import_batch_id) REFERENCES mdm_import_batches (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mdm_master_records_import_batch_id: %', SQLERRM;
END $$;

-- ===== medical_knowledge =====
CREATE TABLE IF NOT EXISTS medical_knowledge (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE medical_knowledge ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE medical_knowledge ADD COLUMN IF NOT EXISTS knowledge_code VARCHAR(50);
ALTER TABLE medical_knowledge ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE medical_knowledge ADD COLUMN IF NOT EXISTS category VARCHAR(100);
ALTER TABLE medical_knowledge ADD COLUMN IF NOT EXISTS content TEXT;
ALTER TABLE medical_knowledge ADD COLUMN IF NOT EXISTS tags_json TEXT DEFAULT '[]';
ALTER TABLE medical_knowledge ADD COLUMN IF NOT EXISTS evidence_level VARCHAR(10) DEFAULT 'B';
ALTER TABLE medical_knowledge ADD COLUMN IF NOT EXISTS source_pack VARCHAR(50);
ALTER TABLE medical_knowledge ADD COLUMN IF NOT EXISTS version VARCHAR(20) DEFAULT '1.0';
ALTER TABLE medical_knowledge ADD COLUMN IF NOT EXISTS citation_json TEXT DEFAULT '{}';
ALTER TABLE medical_knowledge ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE medical_knowledge ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_medical_knowledge_knowledge_code ON medical_knowledge (knowledge_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_medical_knowledge_knowledge_code'
  ) THEN
    ALTER TABLE medical_knowledge
      ADD CONSTRAINT uq_medical_knowledge_knowledge_code UNIQUE (knowledge_code);
  END IF;
END $$;


-- ===== medical_order_events =====
CREATE TABLE IF NOT EXISTS medical_order_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE medical_order_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE medical_order_events ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE medical_order_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE medical_order_events ADD COLUMN IF NOT EXISTS from_status VARCHAR(50);
ALTER TABLE medical_order_events ADD COLUMN IF NOT EXISTS to_status VARCHAR(50);
ALTER TABLE medical_order_events ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE medical_order_events ADD COLUMN IF NOT EXISTS actor_email VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE medical_order_events ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE medical_order_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_medical_order_events_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_medical_order_events_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE medical_order_events
    ADD CONSTRAINT fk_medical_order_events_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_medical_order_events_medical_order_id: %', SQLERRM;
END $$;

-- ===== medical_orders =====
CREATE TABLE IF NOT EXISTS medical_orders (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS order_code VARCHAR(50);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS marketplace_booking_id VARCHAR(36);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS legacy_order_id VARCHAR(36);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS patient_id VARCHAR(36);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS patient_name VARCHAR(255);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS patient_phone VARCHAR(30);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS diagnostic_service_id VARCHAR(36);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'BOOKED';
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS total_amount FLOAT DEFAULT 0;
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(50);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS barcode_value VARCHAR(100);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS qr_payload VARCHAR(255);
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE medical_orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_medical_orders_order_code ON medical_orders (order_code);
CREATE UNIQUE INDEX IF NOT EXISTS ix_medical_orders_marketplace_booking_id ON medical_orders (marketplace_booking_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_medical_orders_barcode_value ON medical_orders (barcode_value);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_medical_orders_order_code'
  ) THEN
    ALTER TABLE medical_orders
      ADD CONSTRAINT uq_medical_orders_order_code UNIQUE (order_code);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_medical_orders_marketplace_booking_id'
  ) THEN
    ALTER TABLE medical_orders
      ADD CONSTRAINT uq_medical_orders_marketplace_booking_id UNIQUE (marketplace_booking_id);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_medical_orders_barcode_value'
  ) THEN
    ALTER TABLE medical_orders
      ADD CONSTRAINT uq_medical_orders_barcode_value UNIQUE (barcode_value);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.marketplace_bookings') IS NULL THEN
    RAISE NOTICE 'marketplace_bookings missing — skip FK fk_medical_orders_marketplace_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_medical_orders_marketplace_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE medical_orders
    ADD CONSTRAINT fk_medical_orders_marketplace_booking_id
    FOREIGN KEY (marketplace_booking_id) REFERENCES marketplace_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_medical_orders_marketplace_booking_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.orders') IS NULL THEN
    RAISE NOTICE 'orders missing — skip FK fk_medical_orders_legacy_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_medical_orders_legacy_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE medical_orders
    ADD CONSTRAINT fk_medical_orders_legacy_order_id
    FOREIGN KEY (legacy_order_id) REFERENCES orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_medical_orders_legacy_order_id: %', SQLERRM;
END $$;

-- ===== medical_samples =====
CREATE TABLE IF NOT EXISTS medical_samples (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE medical_samples ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE medical_samples ADD COLUMN IF NOT EXISTS sample_code VARCHAR(50);
ALTER TABLE medical_samples ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE medical_samples ADD COLUMN IF NOT EXISTS sample_type VARCHAR(100);
ALTER TABLE medical_samples ADD COLUMN IF NOT EXISTS barcode_value VARCHAR(100);
ALTER TABLE medical_samples ADD COLUMN IF NOT EXISTS qr_payload VARCHAR(255);
ALTER TABLE medical_samples ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'CREATED';
ALTER TABLE medical_samples ADD COLUMN IF NOT EXISTS collected_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE medical_samples ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE medical_samples ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_medical_samples_sample_code ON medical_samples (sample_code);
CREATE UNIQUE INDEX IF NOT EXISTS ix_medical_samples_barcode_value ON medical_samples (barcode_value);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_medical_samples_barcode_value'
  ) THEN
    ALTER TABLE medical_samples
      ADD CONSTRAINT uq_medical_samples_barcode_value UNIQUE (barcode_value);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_medical_samples_sample_code'
  ) THEN
    ALTER TABLE medical_samples
      ADD CONSTRAINT uq_medical_samples_sample_code UNIQUE (sample_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_medical_samples_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_medical_samples_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE medical_samples
    ADD CONSTRAINT fk_medical_samples_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_medical_samples_medical_order_id: %', SQLERRM;
END $$;

-- ===== metric_snapshots =====
CREATE TABLE IF NOT EXISTS metric_snapshots (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS snapshot_code VARCHAR(50);
ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS metric_domain VARCHAR(50);
ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS period_type VARCHAR(20);
ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS period_start TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS period_end TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS metrics_json TEXT;
ALTER TABLE metric_snapshots ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_metric_snapshots_snapshot_code ON metric_snapshots (snapshot_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_metric_snapshots_snapshot_code'
  ) THEN
    ALTER TABLE metric_snapshots
      ADD CONSTRAINT uq_metric_snapshots_snapshot_code UNIQUE (snapshot_code);
  END IF;
END $$;


-- ===== mobile_audit_events =====
CREATE TABLE IF NOT EXISTS mobile_audit_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mobile_audit_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mobile_audit_events ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE mobile_audit_events ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);
ALTER TABLE mobile_audit_events ADD COLUMN IF NOT EXISTS workspace VARCHAR(30);
ALTER TABLE mobile_audit_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(80);
ALTER TABLE mobile_audit_events ADD COLUMN IF NOT EXISTS resource_type VARCHAR(50);
ALTER TABLE mobile_audit_events ADD COLUMN IF NOT EXISTS resource_id VARCHAR(36);
ALTER TABLE mobile_audit_events ADD COLUMN IF NOT EXISTS outcome VARCHAR(30) DEFAULT 'SUCCESS';
ALTER TABLE mobile_audit_events ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(80);
ALTER TABLE mobile_audit_events ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE mobile_audit_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_mobile_audit_events_organization_id ON mobile_audit_events (organization_id);
CREATE INDEX IF NOT EXISTS ix_mobile_audit_events_user_id ON mobile_audit_events (user_id);



-- ===== mobile_devices =====
CREATE TABLE IF NOT EXISTS mobile_devices (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS device_reference VARCHAR(80);
ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);
ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS platform VARCHAR(20);
ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS app_version VARCHAR(30);
ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS notification_token_hash VARCHAR(64);
ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS workspace VARCHAR(30);
ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mobile_devices ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_mobile_devices_device_reference ON mobile_devices (device_reference);
CREATE INDEX IF NOT EXISTS ix_mobile_devices_user_id ON mobile_devices (user_id);
CREATE INDEX IF NOT EXISTS ix_mobile_devices_organization_id ON mobile_devices (organization_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mobile_devices_device_reference'
  ) THEN
    ALTER TABLE mobile_devices
      ADD CONSTRAINT uq_mobile_devices_device_reference UNIQUE (device_reference);
  END IF;
END $$;


-- ===== mp_audit_events =====
CREATE TABLE IF NOT EXISTS mp_audit_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mp_audit_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mp_audit_events ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE mp_audit_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(80);
ALTER TABLE mp_audit_events ADD COLUMN IF NOT EXISTS actor_id VARCHAR(36);
ALTER TABLE mp_audit_events ADD COLUMN IF NOT EXISTS resource_type VARCHAR(50);
ALTER TABLE mp_audit_events ADD COLUMN IF NOT EXISTS resource_id VARCHAR(36);
ALTER TABLE mp_audit_events ADD COLUMN IF NOT EXISTS outcome VARCHAR(30);
ALTER TABLE mp_audit_events ADD COLUMN IF NOT EXISTS details_json TEXT DEFAULT '{}';
ALTER TABLE mp_audit_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_mp_audit_events_organization_id ON mp_audit_events (organization_id);



-- ===== mp_availability =====
CREATE TABLE IF NOT EXISTS mp_availability (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mp_availability ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mp_availability ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE mp_availability ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE mp_availability ADD COLUMN IF NOT EXISTS slot_start TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mp_availability ADD COLUMN IF NOT EXISTS slot_end TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mp_availability ADD COLUMN IF NOT EXISTS capacity INTEGER DEFAULT 1;
ALTER TABLE mp_availability ADD COLUMN IF NOT EXISTS reserved INTEGER DEFAULT 0;
ALTER TABLE mp_availability ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN DEFAULT FALSE;
ALTER TABLE mp_availability ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_mp_availability_organization_id ON mp_availability (organization_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mp_avail_provider_slot'
  ) THEN
    ALTER TABLE mp_availability
      ADD CONSTRAINT uq_mp_avail_provider_slot UNIQUE (provider_id, slot_start);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.mp_providers') IS NULL THEN
    RAISE NOTICE 'mp_providers missing — skip FK fk_mp_availability_provider_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mp_availability_provider_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mp_availability
    ADD CONSTRAINT fk_mp_availability_provider_id
    FOREIGN KEY (provider_id) REFERENCES mp_providers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mp_availability_provider_id: %', SQLERRM;
END $$;

-- ===== mp_bookings =====
CREATE TABLE IF NOT EXISTS mp_bookings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS booking_code VARCHAR(50);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS patient_id VARCHAR(36);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS patient_user_id VARCHAR(36);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS listing_id VARCHAR(36);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS service_type VARCHAR(50);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS appointment_type VARCHAR(50);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS scheduled_start TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS scheduled_end TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS pickup_address TEXT;
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS clinic_address TEXT;
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(30);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS preparation_acknowledged BOOLEAN DEFAULT FALSE;
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS consent_status VARCHAR(30) DEFAULT 'PENDING';
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS pricing_snapshot_id VARCHAR(36);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS booking_status VARCHAR(30) DEFAULT 'DRAFT';
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS collection_job_id VARCHAR(36);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(80);
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mp_bookings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_mp_bookings_booking_code ON mp_bookings (booking_code);
CREATE INDEX IF NOT EXISTS ix_mp_bookings_organization_id ON mp_bookings (organization_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_mp_bookings_idempotency_key ON mp_bookings (idempotency_key);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mp_bookings_idempotency_key'
  ) THEN
    ALTER TABLE mp_bookings
      ADD CONSTRAINT uq_mp_bookings_idempotency_key UNIQUE (idempotency_key);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mp_bookings_booking_code'
  ) THEN
    ALTER TABLE mp_bookings
      ADD CONSTRAINT uq_mp_bookings_booking_code UNIQUE (booking_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.mp_pricing_snapshots') IS NULL THEN
    RAISE NOTICE 'mp_pricing_snapshots missing — skip FK fk_mp_bookings_pricing_snapshot_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mp_bookings_pricing_snapshot_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mp_bookings
    ADD CONSTRAINT fk_mp_bookings_pricing_snapshot_id
    FOREIGN KEY (pricing_snapshot_id) REFERENCES mp_pricing_snapshots (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mp_bookings_pricing_snapshot_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.mp_listings') IS NULL THEN
    RAISE NOTICE 'mp_listings missing — skip FK fk_mp_bookings_listing_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mp_bookings_listing_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mp_bookings
    ADD CONSTRAINT fk_mp_bookings_listing_id
    FOREIGN KEY (listing_id) REFERENCES mp_listings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mp_bookings_listing_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.mp_providers') IS NULL THEN
    RAISE NOTICE 'mp_providers missing — skip FK fk_mp_bookings_provider_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mp_bookings_provider_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mp_bookings
    ADD CONSTRAINT fk_mp_bookings_provider_id
    FOREIGN KEY (provider_id) REFERENCES mp_providers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mp_bookings_provider_id: %', SQLERRM;
END $$;

-- ===== mp_listings =====
CREATE TABLE IF NOT EXISTS mp_listings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS service_id VARCHAR(36);
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS listing_code VARCHAR(80);
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'DRAFT';
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS base_price NUMERIC(12, 2) DEFAULT 0;
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'VND';
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS home_collection_available BOOLEAN DEFAULT FALSE;
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS service_radius_km FLOAT;
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS price_updated_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS partner_consent BOOLEAN DEFAULT FALSE;
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mp_listings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_mp_listings_organization_id ON mp_listings (organization_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_mp_listings_listing_code ON mp_listings (listing_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mp_listings_listing_code'
  ) THEN
    ALTER TABLE mp_listings
      ADD CONSTRAINT uq_mp_listings_listing_code UNIQUE (listing_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.mp_providers') IS NULL THEN
    RAISE NOTICE 'mp_providers missing — skip FK fk_mp_listings_provider_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mp_listings_provider_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mp_listings
    ADD CONSTRAINT fk_mp_listings_provider_id
    FOREIGN KEY (provider_id) REFERENCES mp_providers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mp_listings_provider_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.mp_services') IS NULL THEN
    RAISE NOTICE 'mp_services missing — skip FK fk_mp_listings_service_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mp_listings_service_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mp_listings
    ADD CONSTRAINT fk_mp_listings_service_id
    FOREIGN KEY (service_id) REFERENCES mp_services (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mp_listings_service_id: %', SQLERRM;
END $$;

-- ===== mp_payments =====
CREATE TABLE IF NOT EXISTS mp_payments (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS booking_id VARCHAR(36);
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS payment_reference VARCHAR(80);
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS amount NUMERIC(12, 2);
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'VND';
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS payment_method VARCHAR(30) DEFAULT 'QR_BANK_TRANSFER';
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'CREATED';
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS qr_payload TEXT;
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS provider_code VARCHAR(50);
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS webhook_idempotency_key VARCHAR(80);
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS reconciliation_json TEXT DEFAULT '{}';
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mp_payments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_mp_payments_organization_id ON mp_payments (organization_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_mp_payments_payment_reference ON mp_payments (payment_reference);
CREATE UNIQUE INDEX IF NOT EXISTS ix_mp_payments_webhook_idempotency_key ON mp_payments (webhook_idempotency_key);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mp_payments_webhook_idempotency_key'
  ) THEN
    ALTER TABLE mp_payments
      ADD CONSTRAINT uq_mp_payments_webhook_idempotency_key UNIQUE (webhook_idempotency_key);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mp_payments_payment_reference'
  ) THEN
    ALTER TABLE mp_payments
      ADD CONSTRAINT uq_mp_payments_payment_reference UNIQUE (payment_reference);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.mp_bookings') IS NULL THEN
    RAISE NOTICE 'mp_bookings missing — skip FK fk_mp_payments_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mp_payments_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mp_payments
    ADD CONSTRAINT fk_mp_payments_booking_id
    FOREIGN KEY (booking_id) REFERENCES mp_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mp_payments_booking_id: %', SQLERRM;
END $$;

-- ===== mp_pricing_snapshots =====
CREATE TABLE IF NOT EXISTS mp_pricing_snapshots (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mp_pricing_snapshots ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mp_pricing_snapshots ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE mp_pricing_snapshots ADD COLUMN IF NOT EXISTS listing_id VARCHAR(36);
ALTER TABLE mp_pricing_snapshots ADD COLUMN IF NOT EXISTS components_json TEXT;
ALTER TABLE mp_pricing_snapshots ADD COLUMN IF NOT EXISTS rule_versions_json TEXT DEFAULT '{}';
ALTER TABLE mp_pricing_snapshots ADD COLUMN IF NOT EXISTS total_amount NUMERIC(12, 2);
ALTER TABLE mp_pricing_snapshots ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'VND';
ALTER TABLE mp_pricing_snapshots ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.mp_listings') IS NULL THEN
    RAISE NOTICE 'mp_listings missing — skip FK fk_mp_pricing_snapshots_listing_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mp_pricing_snapshots_listing_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mp_pricing_snapshots
    ADD CONSTRAINT fk_mp_pricing_snapshots_listing_id
    FOREIGN KEY (listing_id) REFERENCES mp_listings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mp_pricing_snapshots_listing_id: %', SQLERRM;
END $$;

-- ===== mp_promotions =====
CREATE TABLE IF NOT EXISTS mp_promotions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS promotion_code VARCHAR(50);
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS promotion_type VARCHAR(30) DEFAULT 'PLATFORM';
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS discount_percent NUMERIC(5, 2);
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS discount_amount NUMERIC(12, 2);
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS min_order_amount NUMERIC(12, 2) DEFAULT 0;
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS usage_limit INTEGER;
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS per_patient_limit INTEGER DEFAULT 1;
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0;
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS starts_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS ends_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS stacking_policy VARCHAR(20) DEFAULT 'NONE';
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE mp_promotions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_mp_promotions_organization_id ON mp_promotions (organization_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mp_promo_org_code'
  ) THEN
    ALTER TABLE mp_promotions
      ADD CONSTRAINT uq_mp_promo_org_code UNIQUE (organization_id, promotion_code);
  END IF;
END $$;


-- ===== mp_providers =====
CREATE TABLE IF NOT EXISTS mp_providers (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS provider_code VARCHAR(80);
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS provider_name VARCHAR(255);
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS provider_type VARCHAR(50);
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS verified BOOLEAN DEFAULT FALSE;
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS latitude FLOAT;
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS longitude FLOAT;
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS working_hours_json TEXT DEFAULT '{}';
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS service_areas_json TEXT DEFAULT '[]';
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS certifications_json TEXT DEFAULT '[]';
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS specialties_json TEXT DEFAULT '[]';
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS rating_avg FLOAT DEFAULT 0.0;
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS rating_count INTEGER DEFAULT 0;
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS turnaround_hours INTEGER;
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS collection_methods_json TEXT DEFAULT '[]';
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS payment_methods_json TEXT DEFAULT '[]';
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS cancellation_policy TEXT;
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS public_status VARCHAR(30) DEFAULT 'ACTIVE';
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE mp_providers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_mp_providers_organization_id ON mp_providers (organization_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_mp_providers_provider_code ON mp_providers (provider_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mp_providers_provider_code'
  ) THEN
    ALTER TABLE mp_providers
      ADD CONSTRAINT uq_mp_providers_provider_code UNIQUE (provider_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_mp_providers_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mp_providers_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mp_providers
    ADD CONSTRAINT fk_mp_providers_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mp_providers_partner_id: %', SQLERRM;
END $$;

-- ===== mp_reviews =====
CREATE TABLE IF NOT EXISTS mp_reviews (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mp_reviews ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mp_reviews ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE mp_reviews ADD COLUMN IF NOT EXISTS booking_id VARCHAR(36);
ALTER TABLE mp_reviews ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE mp_reviews ADD COLUMN IF NOT EXISTS patient_user_id VARCHAR(36);
ALTER TABLE mp_reviews ADD COLUMN IF NOT EXISTS rating INTEGER;
ALTER TABLE mp_reviews ADD COLUMN IF NOT EXISTS review_text TEXT;
ALTER TABLE mp_reviews ADD COLUMN IF NOT EXISTS moderation_status VARCHAR(20) DEFAULT 'PENDING';
ALTER TABLE mp_reviews ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_mp_reviews_booking_id ON mp_reviews (booking_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mp_reviews_booking_id'
  ) THEN
    ALTER TABLE mp_reviews
      ADD CONSTRAINT uq_mp_reviews_booking_id UNIQUE (booking_id);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.mp_providers') IS NULL THEN
    RAISE NOTICE 'mp_providers missing — skip FK fk_mp_reviews_provider_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mp_reviews_provider_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mp_reviews
    ADD CONSTRAINT fk_mp_reviews_provider_id
    FOREIGN KEY (provider_id) REFERENCES mp_providers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mp_reviews_provider_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.mp_bookings') IS NULL THEN
    RAISE NOTICE 'mp_bookings missing — skip FK fk_mp_reviews_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_mp_reviews_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE mp_reviews
    ADD CONSTRAINT fk_mp_reviews_booking_id
    FOREIGN KEY (booking_id) REFERENCES mp_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_mp_reviews_booking_id: %', SQLERRM;
END $$;

-- ===== mp_services =====
CREATE TABLE IF NOT EXISTS mp_services (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE mp_services ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE mp_services ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE mp_services ADD COLUMN IF NOT EXISTS service_code VARCHAR(80);
ALTER TABLE mp_services ADD COLUMN IF NOT EXISTS service_name VARCHAR(255);
ALTER TABLE mp_services ADD COLUMN IF NOT EXISTS service_type VARCHAR(50);
ALTER TABLE mp_services ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE mp_services ADD COLUMN IF NOT EXISTS preparation_instructions TEXT;
ALTER TABLE mp_services ADD COLUMN IF NOT EXISTS sample_requirements TEXT;
ALTER TABLE mp_services ADD COLUMN IF NOT EXISTS duration_minutes INTEGER DEFAULT 30;
ALTER TABLE mp_services ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE mp_services ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_mp_services_organization_id ON mp_services (organization_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_mp_service_org_code'
  ) THEN
    ALTER TABLE mp_services
      ADD CONSTRAINT uq_mp_service_org_code UNIQUE (organization_id, service_code);
  END IF;
END $$;


-- ===== nc_notification_channels =====
CREATE TABLE IF NOT EXISTS nc_notification_channels (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE nc_notification_channels ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE nc_notification_channels ADD COLUMN IF NOT EXISTS channel_code VARCHAR(50);
ALTER TABLE nc_notification_channels ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE nc_notification_channels ADD COLUMN IF NOT EXISTS provider_type VARCHAR(50);
ALTER TABLE nc_notification_channels ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE nc_notification_channels ADD COLUMN IF NOT EXISTS config_json TEXT DEFAULT '{}';
ALTER TABLE nc_notification_channels ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_nc_notification_channels_channel_code ON nc_notification_channels (channel_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_nc_notification_channels_channel_code'
  ) THEN
    ALTER TABLE nc_notification_channels
      ADD CONSTRAINT uq_nc_notification_channels_channel_code UNIQUE (channel_code);
  END IF;
END $$;


-- ===== nc_notification_deliveries =====
CREATE TABLE IF NOT EXISTS nc_notification_deliveries (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE nc_notification_deliveries ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE nc_notification_deliveries ADD COLUMN IF NOT EXISTS notification_id VARCHAR(36);
ALTER TABLE nc_notification_deliveries ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE nc_notification_deliveries ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'QUEUED';
ALTER TABLE nc_notification_deliveries ADD COLUMN IF NOT EXISTS provider_message_id VARCHAR(100);
ALTER TABLE nc_notification_deliveries ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE nc_notification_deliveries ADD COLUMN IF NOT EXISTS latency_ms FLOAT DEFAULT 0;
ALTER TABLE nc_notification_deliveries ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE nc_notification_deliveries ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.nc_notification_providers') IS NULL THEN
    RAISE NOTICE 'nc_notification_providers missing — skip FK fk_nc_notification_deliveries_provider_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_nc_notification_deliveries_provider_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE nc_notification_deliveries
    ADD CONSTRAINT fk_nc_notification_deliveries_provider_id
    FOREIGN KEY (provider_id) REFERENCES nc_notification_providers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_nc_notification_deliveries_provider_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.nc_notifications') IS NULL THEN
    RAISE NOTICE 'nc_notifications missing — skip FK fk_nc_notification_deliveries_notification_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_nc_notification_deliveries_notification_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE nc_notification_deliveries
    ADD CONSTRAINT fk_nc_notification_deliveries_notification_id
    FOREIGN KEY (notification_id) REFERENCES nc_notifications (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_nc_notification_deliveries_notification_id: %', SQLERRM;
END $$;

-- ===== nc_notification_preferences =====
CREATE TABLE IF NOT EXISTS nc_notification_preferences (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE nc_notification_preferences ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE nc_notification_preferences ADD COLUMN IF NOT EXISTS user_id VARCHAR(100);
ALTER TABLE nc_notification_preferences ADD COLUMN IF NOT EXISTS email_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE nc_notification_preferences ADD COLUMN IF NOT EXISTS sms_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE nc_notification_preferences ADD COLUMN IF NOT EXISTS push_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE nc_notification_preferences ADD COLUMN IF NOT EXISTS zalo_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE nc_notification_preferences ADD COLUMN IF NOT EXISTS webhook_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE nc_notification_preferences ADD COLUMN IF NOT EXISTS mute_start_hour INTEGER;
ALTER TABLE nc_notification_preferences ADD COLUMN IF NOT EXISTS mute_end_hour INTEGER;
ALTER TABLE nc_notification_preferences ADD COLUMN IF NOT EXISTS critical_override BOOLEAN DEFAULT TRUE;
ALTER TABLE nc_notification_preferences ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_nc_notification_preferences_user_id ON nc_notification_preferences (user_id);



-- ===== nc_notification_providers =====
CREATE TABLE IF NOT EXISTS nc_notification_providers (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE nc_notification_providers ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE nc_notification_providers ADD COLUMN IF NOT EXISTS provider_code VARCHAR(50);
ALTER TABLE nc_notification_providers ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE nc_notification_providers ADD COLUMN IF NOT EXISTS channel VARCHAR(50);
ALTER TABLE nc_notification_providers ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE nc_notification_providers ADD COLUMN IF NOT EXISTS health_status VARCHAR(50) DEFAULT 'OK';
ALTER TABLE nc_notification_providers ADD COLUMN IF NOT EXISTS config_json TEXT DEFAULT '{}';
ALTER TABLE nc_notification_providers ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_nc_notification_providers_provider_code ON nc_notification_providers (provider_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_nc_notification_providers_provider_code'
  ) THEN
    ALTER TABLE nc_notification_providers
      ADD CONSTRAINT uq_nc_notification_providers_provider_code UNIQUE (provider_code);
  END IF;
END $$;


-- ===== nc_notification_retries =====
CREATE TABLE IF NOT EXISTS nc_notification_retries (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE nc_notification_retries ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE nc_notification_retries ADD COLUMN IF NOT EXISTS notification_id VARCHAR(36);
ALTER TABLE nc_notification_retries ADD COLUMN IF NOT EXISTS attempt_number INTEGER DEFAULT 1;
ALTER TABLE nc_notification_retries ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'RETRY';
ALTER TABLE nc_notification_retries ADD COLUMN IF NOT EXISTS next_retry_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE nc_notification_retries ADD COLUMN IF NOT EXISTS backoff_seconds INTEGER DEFAULT 60;
ALTER TABLE nc_notification_retries ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE nc_notification_retries ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.nc_notifications') IS NULL THEN
    RAISE NOTICE 'nc_notifications missing — skip FK fk_nc_notification_retries_notification_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_nc_notification_retries_notification_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE nc_notification_retries
    ADD CONSTRAINT fk_nc_notification_retries_notification_id
    FOREIGN KEY (notification_id) REFERENCES nc_notifications (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_nc_notification_retries_notification_id: %', SQLERRM;
END $$;

-- ===== nc_notification_templates =====
CREATE TABLE IF NOT EXISTS nc_notification_templates (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE nc_notification_templates ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE nc_notification_templates ADD COLUMN IF NOT EXISTS template_code VARCHAR(50);
ALTER TABLE nc_notification_templates ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE nc_notification_templates ADD COLUMN IF NOT EXISTS channel VARCHAR(50);
ALTER TABLE nc_notification_templates ADD COLUMN IF NOT EXISTS language VARCHAR(20) DEFAULT 'vi';
ALTER TABLE nc_notification_templates ADD COLUMN IF NOT EXISTS subject VARCHAR(255);
ALTER TABLE nc_notification_templates ADD COLUMN IF NOT EXISTS body TEXT;
ALTER TABLE nc_notification_templates ADD COLUMN IF NOT EXISTS variables_json TEXT DEFAULT '[]';
ALTER TABLE nc_notification_templates ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE nc_notification_templates ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_nc_notification_templates_template_code ON nc_notification_templates (template_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_nc_notification_templates_template_code'
  ) THEN
    ALTER TABLE nc_notification_templates
      ADD CONSTRAINT uq_nc_notification_templates_template_code UNIQUE (template_code);
  END IF;
END $$;


-- ===== nc_notifications =====
CREATE TABLE IF NOT EXISTS nc_notifications (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS notification_code VARCHAR(50);
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS channel VARCHAR(50);
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS recipient VARCHAR(255);
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS subject VARCHAR(255);
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS body TEXT;
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'QUEUED';
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'NORMAL';
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS template_id VARCHAR(36);
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS provider_id VARCHAR(36);
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS metadata_json TEXT DEFAULT '{}';
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS latency_ms FLOAT DEFAULT 0;
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE nc_notifications ADD COLUMN IF NOT EXISTS sent_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_nc_notifications_notification_code ON nc_notifications (notification_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_nc_notifications_notification_code'
  ) THEN
    ALTER TABLE nc_notifications
      ADD CONSTRAINT uq_nc_notifications_notification_code UNIQUE (notification_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.nc_notification_providers') IS NULL THEN
    RAISE NOTICE 'nc_notification_providers missing — skip FK fk_nc_notifications_provider_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_nc_notifications_provider_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE nc_notifications
    ADD CONSTRAINT fk_nc_notifications_provider_id
    FOREIGN KEY (provider_id) REFERENCES nc_notification_providers (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_nc_notifications_provider_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.nc_notification_templates') IS NULL THEN
    RAISE NOTICE 'nc_notification_templates missing — skip FK fk_nc_notifications_template_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_nc_notifications_template_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE nc_notifications
    ADD CONSTRAINT fk_nc_notifications_template_id
    FOREIGN KEY (template_id) REFERENCES nc_notification_templates (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_nc_notifications_template_id: %', SQLERRM;
END $$;

-- ===== notification_deliveries =====
CREATE TABLE IF NOT EXISTS notification_deliveries (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS notification_id VARCHAR(36);
ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS recipient_id VARCHAR(36);
ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS channel VARCHAR(50);
ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS provider_message_id VARCHAR(100);
ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS sent_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE notification_deliveries ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.notifications') IS NULL THEN
    RAISE NOTICE 'notifications missing — skip FK fk_notification_deliveries_notification_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_notification_deliveries_notification_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE notification_deliveries
    ADD CONSTRAINT fk_notification_deliveries_notification_id
    FOREIGN KEY (notification_id) REFERENCES notifications (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_notification_deliveries_notification_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.notification_recipients') IS NULL THEN
    RAISE NOTICE 'notification_recipients missing — skip FK fk_notification_deliveries_recipient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_notification_deliveries_recipient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE notification_deliveries
    ADD CONSTRAINT fk_notification_deliveries_recipient_id
    FOREIGN KEY (recipient_id) REFERENCES notification_recipients (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_notification_deliveries_recipient_id: %', SQLERRM;
END $$;

-- ===== notification_preferences =====
CREATE TABLE IF NOT EXISTS notification_preferences (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);
ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS channel VARCHAR(50);
ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS template_code VARCHAR(50);
ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS is_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE notification_preferences ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_notification_pref'
  ) THEN
    ALTER TABLE notification_preferences
      ADD CONSTRAINT uq_notification_pref UNIQUE (user_id, channel, template_code);
  END IF;
END $$;


-- ===== notification_recipients =====
CREATE TABLE IF NOT EXISTS notification_recipients (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE notification_recipients ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE notification_recipients ADD COLUMN IF NOT EXISTS notification_id VARCHAR(36);
ALTER TABLE notification_recipients ADD COLUMN IF NOT EXISTS recipient_type VARCHAR(50) DEFAULT 'USER';
ALTER TABLE notification_recipients ADD COLUMN IF NOT EXISTS recipient_id VARCHAR(36);
ALTER TABLE notification_recipients ADD COLUMN IF NOT EXISTS recipient_name VARCHAR(255);
ALTER TABLE notification_recipients ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE notification_recipients ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
ALTER TABLE notification_recipients ADD COLUMN IF NOT EXISTS zalo_id VARCHAR(100);
ALTER TABLE notification_recipients ADD COLUMN IF NOT EXISTS push_token VARCHAR(255);
ALTER TABLE notification_recipients ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.notifications') IS NULL THEN
    RAISE NOTICE 'notifications missing — skip FK fk_notification_recipients_notification_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_notification_recipients_notification_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE notification_recipients
    ADD CONSTRAINT fk_notification_recipients_notification_id
    FOREIGN KEY (notification_id) REFERENCES notifications (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_notification_recipients_notification_id: %', SQLERRM;
END $$;

-- ===== notification_templates =====
CREATE TABLE IF NOT EXISTS notification_templates (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS template_code VARCHAR(50);
ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS subject VARCHAR(255);
ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS body TEXT;
ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS sms_body TEXT;
ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS push_title VARCHAR(255);
ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS push_body TEXT;
ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS zalo_body TEXT;
ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS default_channels VARCHAR(255) DEFAULT 'IN_APP,EMAIL';
ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE notification_templates ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_notification_templates_template_code ON notification_templates (template_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_notification_templates_template_code'
  ) THEN
    ALTER TABLE notification_templates
      ADD CONSTRAINT uq_notification_templates_template_code UNIQUE (template_code);
  END IF;
END $$;


-- ===== notifications =====
CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE notifications ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS notification_code VARCHAR(50);
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS template_code VARCHAR(50);
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS subject VARCHAR(255);
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS body TEXT;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS priority VARCHAR(20) DEFAULT 'NORMAL';
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS reference_type VARCHAR(50);
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS reference_id VARCHAR(36);
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS sent_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_notifications_notification_code ON notifications (notification_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_notifications_notification_code'
  ) THEN
    ALTER TABLE notifications
      ADD CONSTRAINT uq_notifications_notification_code UNIQUE (notification_code);
  END IF;
END $$;


-- ===== obs_alerts =====
CREATE TABLE IF NOT EXISTS obs_alerts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE obs_alerts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE obs_alerts ADD COLUMN IF NOT EXISTS alert_code VARCHAR(50);
ALTER TABLE obs_alerts ADD COLUMN IF NOT EXISTS rule_code VARCHAR(100);
ALTER TABLE obs_alerts ADD COLUMN IF NOT EXISTS severity VARCHAR(50) DEFAULT 'MEDIUM';
ALTER TABLE obs_alerts ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE obs_alerts ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'OPEN';
ALTER TABLE obs_alerts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_obs_alerts_alert_code ON obs_alerts (alert_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_obs_alerts_alert_code'
  ) THEN
    ALTER TABLE obs_alerts
      ADD CONSTRAINT uq_obs_alerts_alert_code UNIQUE (alert_code);
  END IF;
END $$;


-- ===== obs_audit_actors =====
CREATE TABLE IF NOT EXISTS obs_audit_actors (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE obs_audit_actors ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE obs_audit_actors ADD COLUMN IF NOT EXISTS actor_code VARCHAR(50);
ALTER TABLE obs_audit_actors ADD COLUMN IF NOT EXISTS actor_type VARCHAR(50);
ALTER TABLE obs_audit_actors ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);
ALTER TABLE obs_audit_actors ADD COLUMN IF NOT EXISTS user_id VARCHAR(100);
ALTER TABLE obs_audit_actors ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_obs_audit_actors_actor_code ON obs_audit_actors (actor_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_obs_audit_actors_actor_code'
  ) THEN
    ALTER TABLE obs_audit_actors
      ADD CONSTRAINT uq_obs_audit_actors_actor_code UNIQUE (actor_code);
  END IF;
END $$;


-- ===== obs_audit_events =====
CREATE TABLE IF NOT EXISTS obs_audit_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE obs_audit_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE obs_audit_events ADD COLUMN IF NOT EXISTS event_code VARCHAR(50);
ALTER TABLE obs_audit_events ADD COLUMN IF NOT EXISTS timeline_id VARCHAR(36);
ALTER TABLE obs_audit_events ADD COLUMN IF NOT EXISTS actor_id VARCHAR(36);
ALTER TABLE obs_audit_events ADD COLUMN IF NOT EXISTS resource_id VARCHAR(36);
ALTER TABLE obs_audit_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE obs_audit_events ADD COLUMN IF NOT EXISTS action VARCHAR(100);
ALTER TABLE obs_audit_events ADD COLUMN IF NOT EXISTS module VARCHAR(100);
ALTER TABLE obs_audit_events ADD COLUMN IF NOT EXISTS request_id VARCHAR(100);
ALTER TABLE obs_audit_events ADD COLUMN IF NOT EXISTS trace_id VARCHAR(100);
ALTER TABLE obs_audit_events ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE obs_audit_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_obs_audit_events_event_code ON obs_audit_events (event_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_obs_audit_events_event_code'
  ) THEN
    ALTER TABLE obs_audit_events
      ADD CONSTRAINT uq_obs_audit_events_event_code UNIQUE (event_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.obs_audit_actors') IS NULL THEN
    RAISE NOTICE 'obs_audit_actors missing — skip FK fk_obs_audit_events_actor_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_obs_audit_events_actor_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE obs_audit_events
    ADD CONSTRAINT fk_obs_audit_events_actor_id
    FOREIGN KEY (actor_id) REFERENCES obs_audit_actors (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_obs_audit_events_actor_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.obs_audit_timelines') IS NULL THEN
    RAISE NOTICE 'obs_audit_timelines missing — skip FK fk_obs_audit_events_timeline_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_obs_audit_events_timeline_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE obs_audit_events
    ADD CONSTRAINT fk_obs_audit_events_timeline_id
    FOREIGN KEY (timeline_id) REFERENCES obs_audit_timelines (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_obs_audit_events_timeline_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.obs_audit_resources') IS NULL THEN
    RAISE NOTICE 'obs_audit_resources missing — skip FK fk_obs_audit_events_resource_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_obs_audit_events_resource_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE obs_audit_events
    ADD CONSTRAINT fk_obs_audit_events_resource_id
    FOREIGN KEY (resource_id) REFERENCES obs_audit_resources (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_obs_audit_events_resource_id: %', SQLERRM;
END $$;

-- ===== obs_audit_resources =====
CREATE TABLE IF NOT EXISTS obs_audit_resources (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE obs_audit_resources ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE obs_audit_resources ADD COLUMN IF NOT EXISTS resource_code VARCHAR(50);
ALTER TABLE obs_audit_resources ADD COLUMN IF NOT EXISTS resource_type VARCHAR(50);
ALTER TABLE obs_audit_resources ADD COLUMN IF NOT EXISTS resource_id VARCHAR(100);
ALTER TABLE obs_audit_resources ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);
ALTER TABLE obs_audit_resources ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_obs_audit_resources_resource_code ON obs_audit_resources (resource_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_obs_audit_resources_resource_code'
  ) THEN
    ALTER TABLE obs_audit_resources
      ADD CONSTRAINT uq_obs_audit_resources_resource_code UNIQUE (resource_code);
  END IF;
END $$;


-- ===== obs_audit_timelines =====
CREATE TABLE IF NOT EXISTS obs_audit_timelines (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE obs_audit_timelines ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE obs_audit_timelines ADD COLUMN IF NOT EXISTS timeline_code VARCHAR(50);
ALTER TABLE obs_audit_timelines ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE obs_audit_timelines ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE obs_audit_timelines ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_obs_audit_timelines_timeline_code ON obs_audit_timelines (timeline_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_obs_audit_timelines_timeline_code'
  ) THEN
    ALTER TABLE obs_audit_timelines
      ADD CONSTRAINT uq_obs_audit_timelines_timeline_code UNIQUE (timeline_code);
  END IF;
END $$;


-- ===== obs_health_events =====
CREATE TABLE IF NOT EXISTS obs_health_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE obs_health_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE obs_health_events ADD COLUMN IF NOT EXISTS component VARCHAR(100);
ALTER TABLE obs_health_events ADD COLUMN IF NOT EXISTS status VARCHAR(50);
ALTER TABLE obs_health_events ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE obs_health_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== obs_metric_snapshots =====
CREATE TABLE IF NOT EXISTS obs_metric_snapshots (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE obs_metric_snapshots ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE obs_metric_snapshots ADD COLUMN IF NOT EXISTS metric_name VARCHAR(100);
ALTER TABLE obs_metric_snapshots ADD COLUMN IF NOT EXISTS metric_type VARCHAR(50) DEFAULT 'counter';
ALTER TABLE obs_metric_snapshots ADD COLUMN IF NOT EXISTS value FLOAT DEFAULT 0;
ALTER TABLE obs_metric_snapshots ADD COLUMN IF NOT EXISTS labels_json TEXT DEFAULT '{}';
ALTER TABLE obs_metric_snapshots ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== ops_backup_artifacts =====
CREATE TABLE IF NOT EXISTS ops_backup_artifacts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_backup_artifacts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_backup_artifacts ADD COLUMN IF NOT EXISTS backup_job_id VARCHAR(36);
ALTER TABLE ops_backup_artifacts ADD COLUMN IF NOT EXISTS artifact_code VARCHAR(50);
ALTER TABLE ops_backup_artifacts ADD COLUMN IF NOT EXISTS storage_path VARCHAR(500);
ALTER TABLE ops_backup_artifacts ADD COLUMN IF NOT EXISTS checksum VARCHAR(128);
ALTER TABLE ops_backup_artifacts ADD COLUMN IF NOT EXISTS size_bytes INTEGER DEFAULT 0;
ALTER TABLE ops_backup_artifacts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ops_backup_artifacts_artifact_code ON ops_backup_artifacts (artifact_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ops_backup_artifacts_artifact_code'
  ) THEN
    ALTER TABLE ops_backup_artifacts
      ADD CONSTRAINT uq_ops_backup_artifacts_artifact_code UNIQUE (artifact_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.ops_backup_jobs') IS NULL THEN
    RAISE NOTICE 'ops_backup_jobs missing — skip FK fk_ops_backup_artifacts_backup_job_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ops_backup_artifacts_backup_job_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ops_backup_artifacts
    ADD CONSTRAINT fk_ops_backup_artifacts_backup_job_id
    FOREIGN KEY (backup_job_id) REFERENCES ops_backup_jobs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ops_backup_artifacts_backup_job_id: %', SQLERRM;
END $$;

-- ===== ops_backup_jobs =====
CREATE TABLE IF NOT EXISTS ops_backup_jobs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_backup_jobs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_backup_jobs ADD COLUMN IF NOT EXISTS backup_code VARCHAR(50);
ALTER TABLE ops_backup_jobs ADD COLUMN IF NOT EXISTS backup_type VARCHAR(50);
ALTER TABLE ops_backup_jobs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'COMPLETED';
ALTER TABLE ops_backup_jobs ADD COLUMN IF NOT EXISTS manifest_json TEXT DEFAULT '{}';
ALTER TABLE ops_backup_jobs ADD COLUMN IF NOT EXISTS retention_days INTEGER DEFAULT 30;
ALTER TABLE ops_backup_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ops_backup_jobs_backup_code ON ops_backup_jobs (backup_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ops_backup_jobs_backup_code'
  ) THEN
    ALTER TABLE ops_backup_jobs
      ADD CONSTRAINT uq_ops_backup_jobs_backup_code UNIQUE (backup_code);
  END IF;
END $$;


-- ===== ops_deployment_checks =====
CREATE TABLE IF NOT EXISTS ops_deployment_checks (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_deployment_checks ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_deployment_checks ADD COLUMN IF NOT EXISTS deployment_id VARCHAR(36);
ALTER TABLE ops_deployment_checks ADD COLUMN IF NOT EXISTS check_code VARCHAR(50);
ALTER TABLE ops_deployment_checks ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE ops_deployment_checks ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PASSED';
ALTER TABLE ops_deployment_checks ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE ops_deployment_checks ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.ops_deployment_records') IS NULL THEN
    RAISE NOTICE 'ops_deployment_records missing — skip FK fk_ops_deployment_checks_deployment_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ops_deployment_checks_deployment_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ops_deployment_checks
    ADD CONSTRAINT fk_ops_deployment_checks_deployment_id
    FOREIGN KEY (deployment_id) REFERENCES ops_deployment_records (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ops_deployment_checks_deployment_id: %', SQLERRM;
END $$;

-- ===== ops_deployment_records =====
CREATE TABLE IF NOT EXISTS ops_deployment_records (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_deployment_records ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_deployment_records ADD COLUMN IF NOT EXISTS deployment_code VARCHAR(50);
ALTER TABLE ops_deployment_records ADD COLUMN IF NOT EXISTS version VARCHAR(50);
ALTER TABLE ops_deployment_records ADD COLUMN IF NOT EXISTS build_sha VARCHAR(100);
ALTER TABLE ops_deployment_records ADD COLUMN IF NOT EXISTS build_time TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ops_deployment_records ADD COLUMN IF NOT EXISTS environment VARCHAR(50) DEFAULT 'production';
ALTER TABLE ops_deployment_records ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'SUCCESS';
ALTER TABLE ops_deployment_records ADD COLUMN IF NOT EXISTS readiness_score FLOAT DEFAULT 100.0;
ALTER TABLE ops_deployment_records ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ops_deployment_records_deployment_code ON ops_deployment_records (deployment_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ops_deployment_records_deployment_code'
  ) THEN
    ALTER TABLE ops_deployment_records
      ADD CONSTRAINT uq_ops_deployment_records_deployment_code UNIQUE (deployment_code);
  END IF;
END $$;


-- ===== ops_deployment_rollback_plans =====
CREATE TABLE IF NOT EXISTS ops_deployment_rollback_plans (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_deployment_rollback_plans ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_deployment_rollback_plans ADD COLUMN IF NOT EXISTS deployment_id VARCHAR(36);
ALTER TABLE ops_deployment_rollback_plans ADD COLUMN IF NOT EXISTS plan_code VARCHAR(50);
ALTER TABLE ops_deployment_rollback_plans ADD COLUMN IF NOT EXISTS target_version VARCHAR(50);
ALTER TABLE ops_deployment_rollback_plans ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'READY';
ALTER TABLE ops_deployment_rollback_plans ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE ops_deployment_rollback_plans ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ops_deployment_rollback_plans_plan_code ON ops_deployment_rollback_plans (plan_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ops_deployment_rollback_plans_plan_code'
  ) THEN
    ALTER TABLE ops_deployment_rollback_plans
      ADD CONSTRAINT uq_ops_deployment_rollback_plans_plan_code UNIQUE (plan_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.ops_deployment_records') IS NULL THEN
    RAISE NOTICE 'ops_deployment_records missing — skip FK fk_ops_deployment_rollback_plans_deployment_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ops_deployment_rollback_plans_deployment_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ops_deployment_rollback_plans
    ADD CONSTRAINT fk_ops_deployment_rollback_plans_deployment_id
    FOREIGN KEY (deployment_id) REFERENCES ops_deployment_records (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ops_deployment_rollback_plans_deployment_id: %', SQLERRM;
END $$;

-- ===== ops_job_execution_logs =====
CREATE TABLE IF NOT EXISTS ops_job_execution_logs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_job_execution_logs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_job_execution_logs ADD COLUMN IF NOT EXISTS job_id VARCHAR(36);
ALTER TABLE ops_job_execution_logs ADD COLUMN IF NOT EXISTS run_id VARCHAR(36);
ALTER TABLE ops_job_execution_logs ADD COLUMN IF NOT EXISTS level VARCHAR(20) DEFAULT 'INFO';
ALTER TABLE ops_job_execution_logs ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE ops_job_execution_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.ops_scheduled_job_runs') IS NULL THEN
    RAISE NOTICE 'ops_scheduled_job_runs missing — skip FK fk_ops_job_execution_logs_run_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ops_job_execution_logs_run_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ops_job_execution_logs
    ADD CONSTRAINT fk_ops_job_execution_logs_run_id
    FOREIGN KEY (run_id) REFERENCES ops_scheduled_job_runs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ops_job_execution_logs_run_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.ops_scheduled_jobs') IS NULL THEN
    RAISE NOTICE 'ops_scheduled_jobs missing — skip FK fk_ops_job_execution_logs_job_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ops_job_execution_logs_job_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ops_job_execution_logs
    ADD CONSTRAINT fk_ops_job_execution_logs_job_id
    FOREIGN KEY (job_id) REFERENCES ops_scheduled_jobs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ops_job_execution_logs_job_id: %', SQLERRM;
END $$;

-- ===== ops_maintenance_windows =====
CREATE TABLE IF NOT EXISTS ops_maintenance_windows (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_maintenance_windows ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_maintenance_windows ADD COLUMN IF NOT EXISTS window_code VARCHAR(50);
ALTER TABLE ops_maintenance_windows ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE ops_maintenance_windows ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE ops_maintenance_windows ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'SCHEDULED';
ALTER TABLE ops_maintenance_windows ADD COLUMN IF NOT EXISTS starts_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ops_maintenance_windows ADD COLUMN IF NOT EXISTS ends_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ops_maintenance_windows ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT FALSE;
ALTER TABLE ops_maintenance_windows ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ops_maintenance_windows_window_code ON ops_maintenance_windows (window_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ops_maintenance_windows_window_code'
  ) THEN
    ALTER TABLE ops_maintenance_windows
      ADD CONSTRAINT uq_ops_maintenance_windows_window_code UNIQUE (window_code);
  END IF;
END $$;


-- ===== ops_restore_jobs =====
CREATE TABLE IF NOT EXISTS ops_restore_jobs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_restore_jobs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_restore_jobs ADD COLUMN IF NOT EXISTS restore_code VARCHAR(50);
ALTER TABLE ops_restore_jobs ADD COLUMN IF NOT EXISTS backup_job_id VARCHAR(36);
ALTER TABLE ops_restore_jobs ADD COLUMN IF NOT EXISTS mode VARCHAR(50) DEFAULT 'DRY_RUN';
ALTER TABLE ops_restore_jobs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE ops_restore_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ops_restore_jobs_restore_code ON ops_restore_jobs (restore_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ops_restore_jobs_restore_code'
  ) THEN
    ALTER TABLE ops_restore_jobs
      ADD CONSTRAINT uq_ops_restore_jobs_restore_code UNIQUE (restore_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.ops_backup_jobs') IS NULL THEN
    RAISE NOTICE 'ops_backup_jobs missing — skip FK fk_ops_restore_jobs_backup_job_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ops_restore_jobs_backup_job_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ops_restore_jobs
    ADD CONSTRAINT fk_ops_restore_jobs_backup_job_id
    FOREIGN KEY (backup_job_id) REFERENCES ops_backup_jobs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ops_restore_jobs_backup_job_id: %', SQLERRM;
END $$;

-- ===== ops_restore_validations =====
CREATE TABLE IF NOT EXISTS ops_restore_validations (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_restore_validations ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_restore_validations ADD COLUMN IF NOT EXISTS restore_job_id VARCHAR(36);
ALTER TABLE ops_restore_validations ADD COLUMN IF NOT EXISTS validation_code VARCHAR(50);
ALTER TABLE ops_restore_validations ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PASSED';
ALTER TABLE ops_restore_validations ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE ops_restore_validations ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ops_restore_validations_validation_code ON ops_restore_validations (validation_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ops_restore_validations_validation_code'
  ) THEN
    ALTER TABLE ops_restore_validations
      ADD CONSTRAINT uq_ops_restore_validations_validation_code UNIQUE (validation_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.ops_restore_jobs') IS NULL THEN
    RAISE NOTICE 'ops_restore_jobs missing — skip FK fk_ops_restore_validations_restore_job_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ops_restore_validations_restore_job_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ops_restore_validations
    ADD CONSTRAINT fk_ops_restore_validations_restore_job_id
    FOREIGN KEY (restore_job_id) REFERENCES ops_restore_jobs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ops_restore_validations_restore_job_id: %', SQLERRM;
END $$;

-- ===== ops_scheduled_job_locks =====
CREATE TABLE IF NOT EXISTS ops_scheduled_job_locks (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_scheduled_job_locks ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_scheduled_job_locks ADD COLUMN IF NOT EXISTS job_id VARCHAR(36);
ALTER TABLE ops_scheduled_job_locks ADD COLUMN IF NOT EXISTS lock_token VARCHAR(100);
ALTER TABLE ops_scheduled_job_locks ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ops_scheduled_job_locks ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ops_scheduled_job_locks_job_id ON ops_scheduled_job_locks (job_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ops_scheduled_job_locks_job_id'
  ) THEN
    ALTER TABLE ops_scheduled_job_locks
      ADD CONSTRAINT uq_ops_scheduled_job_locks_job_id UNIQUE (job_id);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.ops_scheduled_jobs') IS NULL THEN
    RAISE NOTICE 'ops_scheduled_jobs missing — skip FK fk_ops_scheduled_job_locks_job_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ops_scheduled_job_locks_job_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ops_scheduled_job_locks
    ADD CONSTRAINT fk_ops_scheduled_job_locks_job_id
    FOREIGN KEY (job_id) REFERENCES ops_scheduled_jobs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ops_scheduled_job_locks_job_id: %', SQLERRM;
END $$;

-- ===== ops_scheduled_job_runs =====
CREATE TABLE IF NOT EXISTS ops_scheduled_job_runs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_scheduled_job_runs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_scheduled_job_runs ADD COLUMN IF NOT EXISTS job_id VARCHAR(36);
ALTER TABLE ops_scheduled_job_runs ADD COLUMN IF NOT EXISTS run_code VARCHAR(50);
ALTER TABLE ops_scheduled_job_runs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'RUNNING';
ALTER TABLE ops_scheduled_job_runs ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ops_scheduled_job_runs ADD COLUMN IF NOT EXISTS finished_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ops_scheduled_job_runs ADD COLUMN IF NOT EXISTS duration_ms FLOAT DEFAULT 0;
ALTER TABLE ops_scheduled_job_runs ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE ops_scheduled_job_runs ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ops_scheduled_job_runs_run_code ON ops_scheduled_job_runs (run_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ops_scheduled_job_runs_run_code'
  ) THEN
    ALTER TABLE ops_scheduled_job_runs
      ADD CONSTRAINT uq_ops_scheduled_job_runs_run_code UNIQUE (run_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.ops_scheduled_jobs') IS NULL THEN
    RAISE NOTICE 'ops_scheduled_jobs missing — skip FK fk_ops_scheduled_job_runs_job_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ops_scheduled_job_runs_job_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ops_scheduled_job_runs
    ADD CONSTRAINT fk_ops_scheduled_job_runs_job_id
    FOREIGN KEY (job_id) REFERENCES ops_scheduled_jobs (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ops_scheduled_job_runs_job_id: %', SQLERRM;
END $$;

-- ===== ops_scheduled_jobs =====
CREATE TABLE IF NOT EXISTS ops_scheduled_jobs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_scheduled_jobs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_scheduled_jobs ADD COLUMN IF NOT EXISTS job_code VARCHAR(50);
ALTER TABLE ops_scheduled_jobs ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE ops_scheduled_jobs ADD COLUMN IF NOT EXISTS handler VARCHAR(100);
ALTER TABLE ops_scheduled_jobs ADD COLUMN IF NOT EXISTS cron_expression VARCHAR(100);
ALTER TABLE ops_scheduled_jobs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ENABLED';
ALTER TABLE ops_scheduled_jobs ADD COLUMN IF NOT EXISTS timeout_seconds INTEGER DEFAULT 300;
ALTER TABLE ops_scheduled_jobs ADD COLUMN IF NOT EXISTS max_retries INTEGER DEFAULT 3;
ALTER TABLE ops_scheduled_jobs ADD COLUMN IF NOT EXISTS config_json TEXT DEFAULT '{}';
ALTER TABLE ops_scheduled_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ops_scheduled_jobs_job_code ON ops_scheduled_jobs (job_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ops_scheduled_jobs_job_code'
  ) THEN
    ALTER TABLE ops_scheduled_jobs
      ADD CONSTRAINT uq_ops_scheduled_jobs_job_code UNIQUE (job_code);
  END IF;
END $$;


-- ===== ops_secret_rotation_events =====
CREATE TABLE IF NOT EXISTS ops_secret_rotation_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_secret_rotation_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_secret_rotation_events ADD COLUMN IF NOT EXISTS plan_id VARCHAR(36);
ALTER TABLE ops_secret_rotation_events ADD COLUMN IF NOT EXISTS event_code VARCHAR(50);
ALTER TABLE ops_secret_rotation_events ADD COLUMN IF NOT EXISTS action VARCHAR(50);
ALTER TABLE ops_secret_rotation_events ADD COLUMN IF NOT EXISTS fingerprint VARCHAR(128);
ALTER TABLE ops_secret_rotation_events ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE ops_secret_rotation_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ops_secret_rotation_events_event_code ON ops_secret_rotation_events (event_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ops_secret_rotation_events_event_code'
  ) THEN
    ALTER TABLE ops_secret_rotation_events
      ADD CONSTRAINT uq_ops_secret_rotation_events_event_code UNIQUE (event_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.ops_secret_rotation_plans') IS NULL THEN
    RAISE NOTICE 'ops_secret_rotation_plans missing — skip FK fk_ops_secret_rotation_events_plan_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_ops_secret_rotation_events_plan_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE ops_secret_rotation_events
    ADD CONSTRAINT fk_ops_secret_rotation_events_plan_id
    FOREIGN KEY (plan_id) REFERENCES ops_secret_rotation_plans (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_ops_secret_rotation_events_plan_id: %', SQLERRM;
END $$;

-- ===== ops_secret_rotation_plans =====
CREATE TABLE IF NOT EXISTS ops_secret_rotation_plans (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE ops_secret_rotation_plans ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE ops_secret_rotation_plans ADD COLUMN IF NOT EXISTS secret_name VARCHAR(100);
ALTER TABLE ops_secret_rotation_plans ADD COLUMN IF NOT EXISTS fingerprint VARCHAR(128);
ALTER TABLE ops_secret_rotation_plans ADD COLUMN IF NOT EXISTS rotation_interval_days INTEGER DEFAULT 90;
ALTER TABLE ops_secret_rotation_plans ADD COLUMN IF NOT EXISTS last_rotated_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ops_secret_rotation_plans ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE ops_secret_rotation_plans ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE ops_secret_rotation_plans ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_ops_secret_rotation_plans_secret_name ON ops_secret_rotation_plans (secret_name);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_ops_secret_rotation_plans_secret_name'
  ) THEN
    ALTER TABLE ops_secret_rotation_plans
      ADD CONSTRAINT uq_ops_secret_rotation_plans_secret_name UNIQUE (secret_name);
  END IF;
END $$;


-- ===== opsc_customer_requests =====
CREATE TABLE IF NOT EXISTS opsc_customer_requests (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE opsc_customer_requests ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE opsc_customer_requests ADD COLUMN IF NOT EXISTS request_code VARCHAR(50);
ALTER TABLE opsc_customer_requests ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE opsc_customer_requests ADD COLUMN IF NOT EXISTS request_type VARCHAR(50) DEFAULT 'FEATURE';
ALTER TABLE opsc_customer_requests ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE opsc_customer_requests ADD COLUMN IF NOT EXISTS details TEXT;
ALTER TABLE opsc_customer_requests ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE opsc_customer_requests ADD COLUMN IF NOT EXISTS priority VARCHAR(30) DEFAULT 'NORMAL';
ALTER TABLE opsc_customer_requests ADD COLUMN IF NOT EXISTS requested_by VARCHAR(255);
ALTER TABLE opsc_customer_requests ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE opsc_customer_requests ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE opsc_customer_requests ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_opsc_customer_requests_request_code ON opsc_customer_requests (request_code);
CREATE INDEX IF NOT EXISTS ix_opsc_customer_requests_organization_id ON opsc_customer_requests (organization_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_opsc_customer_requests_request_code'
  ) THEN
    ALTER TABLE opsc_customer_requests
      ADD CONSTRAINT uq_opsc_customer_requests_request_code UNIQUE (request_code);
  END IF;
END $$;


-- ===== opsc_support_tickets =====
CREATE TABLE IF NOT EXISTS opsc_support_tickets (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS ticket_code VARCHAR(50);
ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS subject VARCHAR(255);
ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'GENERAL';
ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS priority VARCHAR(30) DEFAULT 'NORMAL';
ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'OPEN';
ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS requester_email VARCHAR(255);
ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS assigned_to VARCHAR(255);
ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE opsc_support_tickets ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_opsc_support_tickets_ticket_code ON opsc_support_tickets (ticket_code);
CREATE INDEX IF NOT EXISTS ix_opsc_support_tickets_organization_id ON opsc_support_tickets (organization_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_opsc_support_tickets_ticket_code'
  ) THEN
    ALTER TABLE opsc_support_tickets
      ADD CONSTRAINT uq_opsc_support_tickets_ticket_code UNIQUE (ticket_code);
  END IF;
END $$;


-- ===== order_items =====
CREATE TABLE IF NOT EXISTS order_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE order_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS test_catalog_id VARCHAR(36);
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS price FLOAT DEFAULT 0;




-- ===== orders =====
CREATE TABLE IF NOT EXISTS orders (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE orders ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_code VARCHAR(50);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS laboratory_id VARCHAR(36);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS company_id VARCHAR(36);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS contract_id VARCHAR(36);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS marketplace_booking_id VARCHAR(36);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS total_amount FLOAT DEFAULT 0;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_order_code ON orders (order_code);
CREATE UNIQUE INDEX IF NOT EXISTS ix_orders_marketplace_booking_id ON orders (marketplace_booking_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_orders_marketplace_booking_id'
  ) THEN
    ALTER TABLE orders
      ADD CONSTRAINT uq_orders_marketplace_booking_id UNIQUE (marketplace_booking_id);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_orders_order_code'
  ) THEN
    ALTER TABLE orders
      ADD CONSTRAINT uq_orders_order_code UNIQUE (order_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.marketplace_bookings') IS NULL THEN
    RAISE NOTICE 'marketplace_bookings missing — skip FK fk_orders_marketplace_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_orders_marketplace_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE orders
    ADD CONSTRAINT fk_orders_marketplace_booking_id
    FOREIGN KEY (marketplace_booking_id) REFERENCES marketplace_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_orders_marketplace_booking_id: %', SQLERRM;
END $$;

-- ===== organization_price_lists =====
CREATE TABLE IF NOT EXISTS organization_price_lists (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE organization_price_lists ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE organization_price_lists ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE organization_price_lists ADD COLUMN IF NOT EXISTS price_list_code VARCHAR(100);
ALTER TABLE organization_price_lists ADD COLUMN IF NOT EXISTS price_tier VARCHAR(30) DEFAULT 'retail';
ALTER TABLE organization_price_lists ADD COLUMN IF NOT EXISTS effective_from VARCHAR(20);
ALTER TABLE organization_price_lists ADD COLUMN IF NOT EXISTS effective_to VARCHAR(20);
ALTER TABLE organization_price_lists ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE;
ALTER TABLE organization_price_lists ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'active';
ALTER TABLE organization_price_lists ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_organization_price_lists_organization_id ON organization_price_lists (organization_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_org_price_tier'
  ) THEN
    ALTER TABLE organization_price_lists
      ADD CONSTRAINT uq_org_price_tier UNIQUE (organization_id, price_tier);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.organizations') IS NULL THEN
    RAISE NOTICE 'organizations missing — skip FK fk_organization_price_lists_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_organization_price_lists_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE organization_price_lists
    ADD CONSTRAINT fk_organization_price_lists_organization_id
    FOREIGN KEY (organization_id) REFERENCES organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_organization_price_lists_organization_id: %', SQLERRM;
END $$;

-- ===== organization_roles =====
CREATE TABLE IF NOT EXISTS organization_roles (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE organization_roles ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE organization_roles ADD COLUMN IF NOT EXISTS role_code VARCHAR(50);
ALTER TABLE organization_roles ADD COLUMN IF NOT EXISTS role_name VARCHAR(100);
ALTER TABLE organization_roles ADD COLUMN IF NOT EXISTS permissions_json TEXT DEFAULT '[]';
ALTER TABLE organization_roles ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE organization_roles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_organization_roles_role_code ON organization_roles (role_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_organization_roles_role_code'
  ) THEN
    ALTER TABLE organization_roles
      ADD CONSTRAINT uq_organization_roles_role_code UNIQUE (role_code);
  END IF;
END $$;


-- ===== organization_users =====
CREATE TABLE IF NOT EXISTS organization_users (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE organization_users ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE organization_users ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE organization_users ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);
ALTER TABLE organization_users ADD COLUMN IF NOT EXISTS role_code VARCHAR(50) DEFAULT 'VIEWER';
ALTER TABLE organization_users ADD COLUMN IF NOT EXISTS active BOOLEAN DEFAULT TRUE;
ALTER TABLE organization_users ADD COLUMN IF NOT EXISTS invited_by VARCHAR(255);
ALTER TABLE organization_users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE organization_users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE organization_users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_organization_users_organization_id ON organization_users (organization_id);
CREATE INDEX IF NOT EXISTS ix_organization_users_user_id ON organization_users (user_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_org_user'
  ) THEN
    ALTER TABLE organization_users
      ADD CONSTRAINT uq_org_user UNIQUE (organization_id, user_id);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.users') IS NULL THEN
    RAISE NOTICE 'users missing — skip FK fk_organization_users_user_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_organization_users_user_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE organization_users
    ADD CONSTRAINT fk_organization_users_user_id
    FOREIGN KEY (user_id) REFERENCES users (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_organization_users_user_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.organizations') IS NULL THEN
    RAISE NOTICE 'organizations missing — skip FK fk_organization_users_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_organization_users_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE organization_users
    ADD CONSTRAINT fk_organization_users_organization_id
    FOREIGN KEY (organization_id) REFERENCES organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_organization_users_organization_id: %', SQLERRM;
END $$;

-- ===== organizations =====
CREATE TABLE IF NOT EXISTS organizations (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE organizations ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS organization_code VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS organization_name VARCHAR(255);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS organization_type VARCHAR(50) DEFAULT 'CLINIC';
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS tax_code VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS business_license VARCHAR(100);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS address VARCHAR(500);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS website VARCHAR(255);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS contact_person VARCHAR(255);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'active';
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_organizations_organization_code ON organizations (organization_code);
CREATE INDEX IF NOT EXISTS ix_organizations_status ON organizations (status);



-- ===== partner_analytics =====
CREATE TABLE IF NOT EXISTS partner_analytics (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_analytics ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_analytics ADD COLUMN IF NOT EXISTS analytics_code VARCHAR(50);
ALTER TABLE partner_analytics ADD COLUMN IF NOT EXISTS period_start TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_analytics ADD COLUMN IF NOT EXISTS period_end TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_analytics ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_analytics ADD COLUMN IF NOT EXISTS orders_total INTEGER DEFAULT 0;
ALTER TABLE partner_analytics ADD COLUMN IF NOT EXISTS revenue_total FLOAT DEFAULT 0;
ALTER TABLE partner_analytics ADD COLUMN IF NOT EXISTS sla_compliance_rate FLOAT DEFAULT 0;
ALTER TABLE partner_analytics ADD COLUMN IF NOT EXISTS metrics_json TEXT DEFAULT '{}';
ALTER TABLE partner_analytics ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_partner_analytics_analytics_code ON partner_analytics (analytics_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_partner_analytics_analytics_code'
  ) THEN
    ALTER TABLE partner_analytics
      ADD CONSTRAINT uq_partner_analytics_analytics_code UNIQUE (analytics_code);
  END IF;
END $$;


-- ===== partner_api_credentials =====
CREATE TABLE IF NOT EXISTS partner_api_credentials (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_api_credentials ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_api_credentials ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_api_credentials ADD COLUMN IF NOT EXISTS client_id VARCHAR(100);
ALTER TABLE partner_api_credentials ADD COLUMN IF NOT EXISTS client_secret_hash VARCHAR(255);
ALTER TABLE partner_api_credentials ADD COLUMN IF NOT EXISTS api_key_hash VARCHAR(255);
ALTER TABLE partner_api_credentials ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE partner_api_credentials ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_api_credentials ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_partner_api_credentials_client_id ON partner_api_credentials (client_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_partner_api_credentials_client_id'
  ) THEN
    ALTER TABLE partner_api_credentials
      ADD CONSTRAINT uq_partner_api_credentials_client_id UNIQUE (client_id);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_partner_api_credentials_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_api_credentials_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_api_credentials
    ADD CONSTRAINT fk_partner_api_credentials_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_api_credentials_partner_id: %', SQLERRM;
END $$;

-- ===== partner_availabilities =====
CREATE TABLE IF NOT EXISTS partner_availabilities (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_availabilities ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_availabilities ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_availabilities ADD COLUMN IF NOT EXISTS date VARCHAR(20);
ALTER TABLE partner_availabilities ADD COLUMN IF NOT EXISTS maximum_daily_capacity INTEGER DEFAULT 50;
ALTER TABLE partner_availabilities ADD COLUMN IF NOT EXISTS booked_count INTEGER DEFAULT 0;
ALTER TABLE partner_availabilities ADD COLUMN IF NOT EXISTS available_slots INTEGER DEFAULT 50;
ALTER TABLE partner_availabilities ADD COLUMN IF NOT EXISTS next_available_time VARCHAR(50);
ALTER TABLE partner_availabilities ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_availabilities ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_partner_availability_date'
  ) THEN
    ALTER TABLE partner_availabilities
      ADD CONSTRAINT uq_partner_availability_date UNIQUE (partner_id, date);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_partner_availabilities_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_availabilities_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_availabilities
    ADD CONSTRAINT fk_partner_availabilities_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_availabilities_partner_id: %', SQLERRM;
END $$;

-- ===== partner_branches =====
CREATE TABLE IF NOT EXISTS partner_branches (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS branch_code VARCHAR(50);
ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS branch_name VARCHAR(255);
ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS city VARCHAR(100);
ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS district VARCHAR(100);
ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS is_primary BOOLEAN DEFAULT FALSE;
ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_branches ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_partner_branches_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_branches_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_branches
    ADD CONSTRAINT fk_partner_branches_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_branches_partner_id: %', SQLERRM;
END $$;

-- ===== partner_capacities =====
CREATE TABLE IF NOT EXISTS partner_capacities (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_capacities ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_capacities ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_capacities ADD COLUMN IF NOT EXISTS date VARCHAR(20);
ALTER TABLE partner_capacities ADD COLUMN IF NOT EXISTS service_type VARCHAR(50) DEFAULT 'COLLECTION';
ALTER TABLE partner_capacities ADD COLUMN IF NOT EXISTS maximum_capacity INTEGER DEFAULT 20;
ALTER TABLE partner_capacities ADD COLUMN IF NOT EXISTS booked_count INTEGER DEFAULT 0;
ALTER TABLE partner_capacities ADD COLUMN IF NOT EXISTS remaining_capacity INTEGER DEFAULT 20;
ALTER TABLE partner_capacities ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE partner_capacities ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_partner_capacity_day_service'
  ) THEN
    ALTER TABLE partner_capacities
      ADD CONSTRAINT uq_partner_capacity_day_service UNIQUE (partner_id, date, service_type);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_partner_capacities_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_capacities_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_capacities
    ADD CONSTRAINT fk_partner_capacities_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_capacities_partner_id: %', SQLERRM;
END $$;

-- ===== partner_contracts =====
CREATE TABLE IF NOT EXISTS partner_contracts (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_contracts ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_contracts ADD COLUMN IF NOT EXISTS contract_code VARCHAR(50);
ALTER TABLE partner_contracts ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE partner_contracts ADD COLUMN IF NOT EXISTS start_date VARCHAR(20);
ALTER TABLE partner_contracts ADD COLUMN IF NOT EXISTS end_date VARCHAR(20);
ALTER TABLE partner_contracts ADD COLUMN IF NOT EXISTS discount_percent FLOAT DEFAULT 0;
ALTER TABLE partner_contracts ADD COLUMN IF NOT EXISTS payment_terms VARCHAR(100);
ALTER TABLE partner_contracts ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'active';
ALTER TABLE partner_contracts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_contracts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_partner_contracts_contract_code ON partner_contracts (contract_code);
CREATE INDEX IF NOT EXISTS ix_partner_contracts_organization_id ON partner_contracts (organization_id);


DO $$
BEGIN
  IF to_regclass('public.organizations') IS NULL THEN
    RAISE NOTICE 'organizations missing — skip FK fk_partner_contracts_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_contracts_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_contracts
    ADD CONSTRAINT fk_partner_contracts_organization_id
    FOREIGN KEY (organization_id) REFERENCES organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_contracts_organization_id: %', SQLERRM;
END $$;

-- ===== partner_coverage_areas =====
CREATE TABLE IF NOT EXISTS partner_coverage_areas (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_coverage_areas ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_coverage_areas ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_coverage_areas ADD COLUMN IF NOT EXISTS branch_id VARCHAR(36);
ALTER TABLE partner_coverage_areas ADD COLUMN IF NOT EXISTS area_name VARCHAR(255);
ALTER TABLE partner_coverage_areas ADD COLUMN IF NOT EXISTS city VARCHAR(100);
ALTER TABLE partner_coverage_areas ADD COLUMN IF NOT EXISTS district VARCHAR(100);
ALTER TABLE partner_coverage_areas ADD COLUMN IF NOT EXISTS radius_km FLOAT;
ALTER TABLE partner_coverage_areas ADD COLUMN IF NOT EXISTS latitude FLOAT;
ALTER TABLE partner_coverage_areas ADD COLUMN IF NOT EXISTS longitude FLOAT;
ALTER TABLE partner_coverage_areas ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.partner_branches') IS NULL THEN
    RAISE NOTICE 'partner_branches missing — skip FK fk_partner_coverage_areas_branch_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_coverage_areas_branch_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_coverage_areas
    ADD CONSTRAINT fk_partner_coverage_areas_branch_id
    FOREIGN KEY (branch_id) REFERENCES partner_branches (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_coverage_areas_branch_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_partner_coverage_areas_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_coverage_areas_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_coverage_areas
    ADD CONSTRAINT fk_partner_coverage_areas_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_coverage_areas_partner_id: %', SQLERRM;
END $$;

-- ===== partner_documents =====
CREATE TABLE IF NOT EXISTS partner_documents (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_documents ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_documents ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_documents ADD COLUMN IF NOT EXISTS document_type VARCHAR(50);
ALTER TABLE partner_documents ADD COLUMN IF NOT EXISTS document_name VARCHAR(255);
ALTER TABLE partner_documents ADD COLUMN IF NOT EXISTS file_reference VARCHAR(500);
ALTER TABLE partner_documents ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE partner_documents ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_documents ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_partner_documents_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_documents_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_documents
    ADD CONSTRAINT fk_partner_documents_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_documents_partner_id: %', SQLERRM;
END $$;

-- ===== partner_operating_hours =====
CREATE TABLE IF NOT EXISTS partner_operating_hours (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_operating_hours ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_operating_hours ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_operating_hours ADD COLUMN IF NOT EXISTS branch_id VARCHAR(36);
ALTER TABLE partner_operating_hours ADD COLUMN IF NOT EXISTS day_of_week INTEGER;
ALTER TABLE partner_operating_hours ADD COLUMN IF NOT EXISTS open_time VARCHAR(10);
ALTER TABLE partner_operating_hours ADD COLUMN IF NOT EXISTS close_time VARCHAR(10);
ALTER TABLE partner_operating_hours ADD COLUMN IF NOT EXISTS is_closed BOOLEAN DEFAULT FALSE;
ALTER TABLE partner_operating_hours ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_partner_operating_hours_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_operating_hours_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_operating_hours
    ADD CONSTRAINT fk_partner_operating_hours_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_operating_hours_partner_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.partner_branches') IS NULL THEN
    RAISE NOTICE 'partner_branches missing — skip FK fk_partner_operating_hours_branch_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_operating_hours_branch_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_operating_hours
    ADD CONSTRAINT fk_partner_operating_hours_branch_id
    FOREIGN KEY (branch_id) REFERENCES partner_branches (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_operating_hours_branch_id: %', SQLERRM;
END $$;

-- ===== partner_sandbox_tokens =====
CREATE TABLE IF NOT EXISTS partner_sandbox_tokens (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_sandbox_tokens ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_sandbox_tokens ADD COLUMN IF NOT EXISTS partner_id VARCHAR(100);
ALTER TABLE partner_sandbox_tokens ADD COLUMN IF NOT EXISTS token_hash VARCHAR(128);
ALTER TABLE partner_sandbox_tokens ADD COLUMN IF NOT EXISTS scopes_json TEXT DEFAULT '[]';
ALTER TABLE partner_sandbox_tokens ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_sandbox_tokens ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_partner_sandbox_tokens_partner_id ON partner_sandbox_tokens (partner_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_partner_sandbox_tokens_token_hash ON partner_sandbox_tokens (token_hash);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_partner_sandbox_tokens_token_hash'
  ) THEN
    ALTER TABLE partner_sandbox_tokens
      ADD CONSTRAINT uq_partner_sandbox_tokens_token_hash UNIQUE (token_hash);
  END IF;
END $$;


-- ===== partner_service_mappings =====
CREATE TABLE IF NOT EXISTS partner_service_mappings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_service_mappings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_service_mappings ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_service_mappings ADD COLUMN IF NOT EXISTS diagnostic_service_id VARCHAR(36);
ALTER TABLE partner_service_mappings ADD COLUMN IF NOT EXISTS partner_service_code VARCHAR(50);
ALTER TABLE partner_service_mappings ADD COLUMN IF NOT EXISTS partner_service_name VARCHAR(255);
ALTER TABLE partner_service_mappings ADD COLUMN IF NOT EXISTS price FLOAT;
ALTER TABLE partner_service_mappings ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'VND';
ALTER TABLE partner_service_mappings ADD COLUMN IF NOT EXISTS turnaround_hours FLOAT;
ALTER TABLE partner_service_mappings ADD COLUMN IF NOT EXISTS home_collection_available BOOLEAN DEFAULT FALSE;
ALTER TABLE partner_service_mappings ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE partner_service_mappings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_service_mappings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_partner_service_mappings_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_service_mappings_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_service_mappings
    ADD CONSTRAINT fk_partner_service_mappings_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_service_mappings_partner_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.diagnostic_services') IS NULL THEN
    RAISE NOTICE 'diagnostic_services missing — skip FK fk_partner_service_mappings_diagnostic_service_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_service_mappings_diagnostic_service_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_service_mappings
    ADD CONSTRAINT fk_partner_service_mappings_diagnostic_service_id
    FOREIGN KEY (diagnostic_service_id) REFERENCES diagnostic_services (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_service_mappings_diagnostic_service_id: %', SQLERRM;
END $$;

-- ===== partner_services =====
CREATE TABLE IF NOT EXISTS partner_services (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_services ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_services ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_services ADD COLUMN IF NOT EXISTS service_code VARCHAR(50);
ALTER TABLE partner_services ADD COLUMN IF NOT EXISTS service_name VARCHAR(255);
ALTER TABLE partner_services ADD COLUMN IF NOT EXISTS catalog_item_code VARCHAR(50);
ALTER TABLE partner_services ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE partner_services ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE partner_services ADD COLUMN IF NOT EXISTS average_result_time_hours FLOAT;
ALTER TABLE partner_services ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_services ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_partner_services_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_services_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_services
    ADD CONSTRAINT fk_partner_services_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_services_partner_id: %', SQLERRM;
END $$;

-- ===== partner_settlements =====
CREATE TABLE IF NOT EXISTS partner_settlements (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_settlements ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_settlements ADD COLUMN IF NOT EXISTS settlement_code VARCHAR(50);
ALTER TABLE partner_settlements ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_settlements ADD COLUMN IF NOT EXISTS period_start VARCHAR(20);
ALTER TABLE partner_settlements ADD COLUMN IF NOT EXISTS period_end VARCHAR(20);
ALTER TABLE partner_settlements ADD COLUMN IF NOT EXISTS gross_amount FLOAT DEFAULT 0;
ALTER TABLE partner_settlements ADD COLUMN IF NOT EXISTS commission_amount FLOAT DEFAULT 0;
ALTER TABLE partner_settlements ADD COLUMN IF NOT EXISTS net_amount FLOAT DEFAULT 0;
ALTER TABLE partner_settlements ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE partner_settlements ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_settlements ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_settlements ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_partner_settlements_settlement_code ON partner_settlements (settlement_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_partner_settlements_settlement_code'
  ) THEN
    ALTER TABLE partner_settlements
      ADD CONSTRAINT uq_partner_settlements_settlement_code UNIQUE (settlement_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_partner_settlements_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_settlements_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_settlements
    ADD CONSTRAINT fk_partner_settlements_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_settlements_partner_id: %', SQLERRM;
END $$;

-- ===== partner_users =====
CREATE TABLE IF NOT EXISTS partner_users (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_users ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_users ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_users ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);
ALTER TABLE partner_users ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE partner_users ADD COLUMN IF NOT EXISTS role VARCHAR(50);
ALTER TABLE partner_users ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'INVITED';
ALTER TABLE partner_users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_partner_users_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_users_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_users
    ADD CONSTRAINT fk_partner_users_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_users_partner_id: %', SQLERRM;
END $$;

-- ===== partner_verification_items =====
CREATE TABLE IF NOT EXISTS partner_verification_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partner_verification_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partner_verification_items ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE partner_verification_items ADD COLUMN IF NOT EXISTS item_type VARCHAR(50);
ALTER TABLE partner_verification_items ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'MISSING';
ALTER TABLE partner_verification_items ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE partner_verification_items ADD COLUMN IF NOT EXISTS verified_by VARCHAR(255);
ALTER TABLE partner_verification_items ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_verification_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partner_verification_items ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.partners') IS NULL THEN
    RAISE NOTICE 'partners missing — skip FK fk_partner_verification_items_partner_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_partner_verification_items_partner_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE partner_verification_items
    ADD CONSTRAINT fk_partner_verification_items_partner_id
    FOREIGN KEY (partner_id) REFERENCES partners (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_partner_verification_items_partner_id: %', SQLERRM;
END $$;

-- ===== partners =====
CREATE TABLE IF NOT EXISTS partners (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE partners ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS partner_code VARCHAR(50);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS partner_type VARCHAR(50);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS legal_name VARCHAR(255);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS tax_code VARCHAR(50);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS license_number VARCHAR(100);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS representative_name VARCHAR(255);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE partners ADD COLUMN IF NOT EXISTS city VARCHAR(100);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS province VARCHAR(100);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS district VARCHAR(100);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'DRAFT';
ALTER TABLE partners ADD COLUMN IF NOT EXISTS verification_note TEXT;
ALTER TABLE partners ADD COLUMN IF NOT EXISTS api_status VARCHAR(50) DEFAULT 'OFFLINE';
ALTER TABLE partners ADD COLUMN IF NOT EXISTS average_result_time_hours FLOAT;
ALTER TABLE partners ADD COLUMN IF NOT EXISTS pickup_sla_minutes INTEGER;
ALTER TABLE partners ADD COLUMN IF NOT EXISTS response_sla_minutes INTEGER;
ALTER TABLE partners ADD COLUMN IF NOT EXISTS working_hours_summary VARCHAR(500);
ALTER TABLE partners ADD COLUMN IF NOT EXISTS rating FLOAT DEFAULT 0.0;
ALTER TABLE partners ADD COLUMN IF NOT EXISTS review_count INTEGER DEFAULT 0;
ALTER TABLE partners ADD COLUMN IF NOT EXISTS completed_orders INTEGER DEFAULT 0;
ALTER TABLE partners ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE partners ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_partners_partner_code ON partners (partner_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_partners_partner_code'
  ) THEN
    ALTER TABLE partners
      ADD CONSTRAINT uq_partners_partner_code UNIQUE (partner_code);
  END IF;
END $$;


-- ===== patient_consents =====
CREATE TABLE IF NOT EXISTS patient_consents (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE patient_consents ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE patient_consents ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE patient_consents ADD COLUMN IF NOT EXISTS consent_type VARCHAR(50);
ALTER TABLE patient_consents ADD COLUMN IF NOT EXISTS consent_version VARCHAR(20) DEFAULT '1.0';
ALTER TABLE patient_consents ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'GRANTED';
ALTER TABLE patient_consents ADD COLUMN IF NOT EXISTS granted_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE patient_consents ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE patient_consents ADD COLUMN IF NOT EXISTS ip_address VARCHAR(50);
ALTER TABLE patient_consents ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE patient_consents ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_patient_consents_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_patient_consents_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE patient_consents
    ADD CONSTRAINT fk_patient_consents_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_patient_consents_patient_id: %', SQLERRM;
END $$;

-- ===== patient_devices =====
CREATE TABLE IF NOT EXISTS patient_devices (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE patient_devices ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE patient_devices ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE patient_devices ADD COLUMN IF NOT EXISTS device_type VARCHAR(50) DEFAULT 'MOBILE';
ALTER TABLE patient_devices ADD COLUMN IF NOT EXISTS device_name VARCHAR(255);
ALTER TABLE patient_devices ADD COLUMN IF NOT EXISTS push_token VARCHAR(255);
ALTER TABLE patient_devices ADD COLUMN IF NOT EXISTS last_seen_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE patient_devices ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE patient_devices ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_patient_devices_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_patient_devices_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE patient_devices
    ADD CONSTRAINT fk_patient_devices_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_patient_devices_patient_id: %', SQLERRM;
END $$;

-- ===== patient_notification_settings =====
CREATE TABLE IF NOT EXISTS patient_notification_settings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE patient_notification_settings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE patient_notification_settings ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE patient_notification_settings ADD COLUMN IF NOT EXISTS channel VARCHAR(50);
ALTER TABLE patient_notification_settings ADD COLUMN IF NOT EXISTS template_code VARCHAR(50);
ALTER TABLE patient_notification_settings ADD COLUMN IF NOT EXISTS is_enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE patient_notification_settings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE patient_notification_settings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_patient_notif_setting'
  ) THEN
    ALTER TABLE patient_notification_settings
      ADD CONSTRAINT uq_patient_notif_setting UNIQUE (patient_id, channel, template_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_patient_notification_settings_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_patient_notification_settings_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE patient_notification_settings
    ADD CONSTRAINT fk_patient_notification_settings_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_patient_notification_settings_patient_id: %', SQLERRM;
END $$;

-- ===== patient_preferences =====
CREATE TABLE IF NOT EXISTS patient_preferences (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE patient_preferences ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE patient_preferences ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE patient_preferences ADD COLUMN IF NOT EXISTS pref_key VARCHAR(100);
ALTER TABLE patient_preferences ADD COLUMN IF NOT EXISTS pref_value TEXT;
ALTER TABLE patient_preferences ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE patient_preferences ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_patient_pref'
  ) THEN
    ALTER TABLE patient_preferences
      ADD CONSTRAINT uq_patient_pref UNIQUE (patient_id, pref_key);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_patient_preferences_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_patient_preferences_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE patient_preferences
    ADD CONSTRAINT fk_patient_preferences_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_patient_preferences_patient_id: %', SQLERRM;
END $$;

-- ===== patient_profiles =====
CREATE TABLE IF NOT EXISTS patient_profiles (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(255);
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'vi';
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'Asia/Ho_Chi_Minh';
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS favorite_doctors_json TEXT DEFAULT '[]';
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS favorite_clinics_json TEXT DEFAULT '[]';
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS family_members_json TEXT DEFAULT '[]';
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS qr_code VARCHAR(100);
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS qr_payload VARCHAR(255);
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS emergency_contact_name VARCHAR(255);
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS emergency_contact_phone VARCHAR(30);
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE patient_profiles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_patient_profiles_patient_id ON patient_profiles (patient_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_patient_profiles_qr_code ON patient_profiles (qr_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_patient_profiles_qr_code'
  ) THEN
    ALTER TABLE patient_profiles
      ADD CONSTRAINT uq_patient_profiles_qr_code UNIQUE (qr_code);
  END IF;
END $$;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_patient_profiles_patient_id'
  ) THEN
    ALTER TABLE patient_profiles
      ADD CONSTRAINT uq_patient_profiles_patient_id UNIQUE (patient_id);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_patient_profiles_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_patient_profiles_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE patient_profiles
    ADD CONSTRAINT fk_patient_profiles_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_patient_profiles_patient_id: %', SQLERRM;
END $$;

-- ===== patients =====
CREATE TABLE IF NOT EXISTS patients (
    patient_code VARCHAR(50) NOT NULL,
    PRIMARY KEY (patient_code)
);

ALTER TABLE patients ADD COLUMN IF NOT EXISTS patient_code VARCHAR(50);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS gender VARCHAR(20);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS date_of_birth VARCHAR(20);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE patients ADD COLUMN IF NOT EXISTS national_id VARCHAR(50);
ALTER TABLE patients ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== payment_methods =====
CREATE TABLE IF NOT EXISTS payment_methods (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS owner_type VARCHAR(50);
ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS owner_id VARCHAR(36);
ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS method_type VARCHAR(50);
ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS provider VARCHAR(50);
ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);
ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS token_ref VARCHAR(255);
ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS last4 VARCHAR(4);
ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE;
ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE payment_methods ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== payment_records =====
CREATE TABLE IF NOT EXISTS payment_records (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE payment_records ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE payment_records ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE payment_records ADD COLUMN IF NOT EXISTS payment_code VARCHAR(50);
ALTER TABLE payment_records ADD COLUMN IF NOT EXISTS amount FLOAT DEFAULT 0;
ALTER TABLE payment_records ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50) DEFAULT 'BANK_TRANSFER';
ALTER TABLE payment_records ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE payment_records ADD COLUMN IF NOT EXISTS transaction_ref VARCHAR(100);
ALTER TABLE payment_records ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE payment_records ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_payment_records_payment_code ON payment_records (payment_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_payment_records_payment_code'
  ) THEN
    ALTER TABLE payment_records
      ADD CONSTRAINT uq_payment_records_payment_code UNIQUE (payment_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.invoices') IS NULL THEN
    RAISE NOTICE 'invoices missing — skip FK fk_payment_records_invoice_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_payment_records_invoice_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE payment_records
    ADD CONSTRAINT fk_payment_records_invoice_id
    FOREIGN KEY (invoice_id) REFERENCES invoices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_payment_records_invoice_id: %', SQLERRM;
END $$;

-- ===== payment_refunds =====
CREATE TABLE IF NOT EXISTS payment_refunds (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE payment_refunds ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE payment_refunds ADD COLUMN IF NOT EXISTS payment_id VARCHAR(36);
ALTER TABLE payment_refunds ADD COLUMN IF NOT EXISTS transaction_id VARCHAR(36);
ALTER TABLE payment_refunds ADD COLUMN IF NOT EXISTS refund_code VARCHAR(50);
ALTER TABLE payment_refunds ADD COLUMN IF NOT EXISTS provider VARCHAR(50);
ALTER TABLE payment_refunds ADD COLUMN IF NOT EXISTS provider_refund_id VARCHAR(100);
ALTER TABLE payment_refunds ADD COLUMN IF NOT EXISTS amount FLOAT DEFAULT 0;
ALTER TABLE payment_refunds ADD COLUMN IF NOT EXISTS reason TEXT;
ALTER TABLE payment_refunds ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE payment_refunds ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE payment_refunds ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_payment_refunds_refund_code ON payment_refunds (refund_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_payment_refunds_refund_code'
  ) THEN
    ALTER TABLE payment_refunds
      ADD CONSTRAINT uq_payment_refunds_refund_code UNIQUE (refund_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.payments') IS NULL THEN
    RAISE NOTICE 'payments missing — skip FK fk_payment_refunds_payment_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_payment_refunds_payment_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE payment_refunds
    ADD CONSTRAINT fk_payment_refunds_payment_id
    FOREIGN KEY (payment_id) REFERENCES payments (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_payment_refunds_payment_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.payment_transactions') IS NULL THEN
    RAISE NOTICE 'payment_transactions missing — skip FK fk_payment_refunds_transaction_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_payment_refunds_transaction_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE payment_refunds
    ADD CONSTRAINT fk_payment_refunds_transaction_id
    FOREIGN KEY (transaction_id) REFERENCES payment_transactions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_payment_refunds_transaction_id: %', SQLERRM;
END $$;

-- ===== payment_transactions =====
CREATE TABLE IF NOT EXISTS payment_transactions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE payment_transactions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE payment_transactions ADD COLUMN IF NOT EXISTS payment_id VARCHAR(36);
ALTER TABLE payment_transactions ADD COLUMN IF NOT EXISTS provider VARCHAR(50);
ALTER TABLE payment_transactions ADD COLUMN IF NOT EXISTS external_transaction_id VARCHAR(100);
ALTER TABLE payment_transactions ADD COLUMN IF NOT EXISTS amount FLOAT DEFAULT 0;
ALTER TABLE payment_transactions ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'VND';
ALTER TABLE payment_transactions ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE payment_transactions ADD COLUMN IF NOT EXISTS raw_response_json TEXT DEFAULT '{}';
ALTER TABLE payment_transactions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE payment_transactions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_payment_transactions_external_transaction_id ON payment_transactions (external_transaction_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_payment_transactions_external_transaction_id'
  ) THEN
    ALTER TABLE payment_transactions
      ADD CONSTRAINT uq_payment_transactions_external_transaction_id UNIQUE (external_transaction_id);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.payments') IS NULL THEN
    RAISE NOTICE 'payments missing — skip FK fk_payment_transactions_payment_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_payment_transactions_payment_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE payment_transactions
    ADD CONSTRAINT fk_payment_transactions_payment_id
    FOREIGN KEY (payment_id) REFERENCES payments (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_payment_transactions_payment_id: %', SQLERRM;
END $$;

-- ===== payment_webhooks =====
CREATE TABLE IF NOT EXISTS payment_webhooks (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE payment_webhooks ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE payment_webhooks ADD COLUMN IF NOT EXISTS provider VARCHAR(50);
ALTER TABLE payment_webhooks ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE payment_webhooks ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE payment_webhooks ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE;
ALTER TABLE payment_webhooks ADD COLUMN IF NOT EXISTS received_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== payments =====
CREATE TABLE IF NOT EXISTS payments (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE payments ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE payments ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE payments ADD COLUMN IF NOT EXISTS amount FLOAT DEFAULT 0;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50) DEFAULT 'BANK_TRANSFER';
ALTER TABLE payments ADD COLUMN IF NOT EXISTS payment_date TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE payments ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PAID';
ALTER TABLE payments ADD COLUMN IF NOT EXISTS provider VARCHAR(50);
ALTER TABLE payments ADD COLUMN IF NOT EXISTS external_transaction_id VARCHAR(100);
ALTER TABLE payments ADD COLUMN IF NOT EXISTS payment_method_id VARCHAR(36);
ALTER TABLE payments ADD COLUMN IF NOT EXISTS metadata_json TEXT DEFAULT '{}';
ALTER TABLE payments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== pilot_knowledge_articles =====
CREATE TABLE IF NOT EXISTS pilot_knowledge_articles (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE pilot_knowledge_articles ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE pilot_knowledge_articles ADD COLUMN IF NOT EXISTS article_code VARCHAR(50);
ALTER TABLE pilot_knowledge_articles ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'FAQ';
ALTER TABLE pilot_knowledge_articles ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE pilot_knowledge_articles ADD COLUMN IF NOT EXISTS body TEXT;
ALTER TABLE pilot_knowledge_articles ADD COLUMN IF NOT EXISTS content_type VARCHAR(30) DEFAULT 'ARTICLE';
ALTER TABLE pilot_knowledge_articles ADD COLUMN IF NOT EXISTS tags VARCHAR(500);
ALTER TABLE pilot_knowledge_articles ADD COLUMN IF NOT EXISTS published BOOLEAN DEFAULT TRUE;
ALTER TABLE pilot_knowledge_articles ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE pilot_knowledge_articles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_pilot_knowledge_articles_article_code ON pilot_knowledge_articles (article_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_pilot_knowledge_articles_article_code'
  ) THEN
    ALTER TABLE pilot_knowledge_articles
      ADD CONSTRAINT uq_pilot_knowledge_articles_article_code UNIQUE (article_code);
  END IF;
END $$;


-- ===== pilot_onboarding_sessions =====
CREATE TABLE IF NOT EXISTS pilot_onboarding_sessions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE pilot_onboarding_sessions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE pilot_onboarding_sessions ADD COLUMN IF NOT EXISTS session_code VARCHAR(50);
ALTER TABLE pilot_onboarding_sessions ADD COLUMN IF NOT EXISTS onboarding_type VARCHAR(50);
ALTER TABLE pilot_onboarding_sessions ADD COLUMN IF NOT EXISTS current_step VARCHAR(50) DEFAULT 'organization';
ALTER TABLE pilot_onboarding_sessions ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'IN_PROGRESS';
ALTER TABLE pilot_onboarding_sessions ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE pilot_onboarding_sessions ADD COLUMN IF NOT EXISTS payload_json TEXT;
ALTER TABLE pilot_onboarding_sessions ADD COLUMN IF NOT EXISTS requester_email VARCHAR(255);
ALTER TABLE pilot_onboarding_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE pilot_onboarding_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE pilot_onboarding_sessions ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_pilot_onboarding_sessions_session_code ON pilot_onboarding_sessions (session_code);
CREATE INDEX IF NOT EXISTS ix_pilot_onboarding_sessions_organization_id ON pilot_onboarding_sessions (organization_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_pilot_onboarding_sessions_session_code'
  ) THEN
    ALTER TABLE pilot_onboarding_sessions
      ADD CONSTRAINT uq_pilot_onboarding_sessions_session_code UNIQUE (session_code);
  END IF;
END $$;


-- ===== pilot_org_setup_sessions =====
CREATE TABLE IF NOT EXISTS pilot_org_setup_sessions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE pilot_org_setup_sessions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE pilot_org_setup_sessions ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE pilot_org_setup_sessions ADD COLUMN IF NOT EXISTS current_step VARCHAR(50) DEFAULT 'organization';
ALTER TABLE pilot_org_setup_sessions ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'IN_PROGRESS';
ALTER TABLE pilot_org_setup_sessions ADD COLUMN IF NOT EXISTS payload_json TEXT;
ALTER TABLE pilot_org_setup_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE pilot_org_setup_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE pilot_org_setup_sessions ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_pilot_org_setup_sessions_organization_id ON pilot_org_setup_sessions (organization_id);



-- ===== pilot_partner_registrations =====
CREATE TABLE IF NOT EXISTS pilot_partner_registrations (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS registration_code VARCHAR(50);
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS partner_type VARCHAR(50);
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS organization_name VARCHAR(255);
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255);
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(30);
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS domain VARCHAR(255);
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS review_note TEXT;
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(255);
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE pilot_partner_registrations ADD COLUMN IF NOT EXISTS activated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_pilot_partner_registrations_registration_code ON pilot_partner_registrations (registration_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_pilot_partner_registrations_registration_code'
  ) THEN
    ALTER TABLE pilot_partner_registrations
      ADD CONSTRAINT uq_pilot_partner_registrations_registration_code UNIQUE (registration_code);
  END IF;
END $$;


-- ===== pilot_scorecard_runs =====
CREATE TABLE IF NOT EXISTS pilot_scorecard_runs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE pilot_scorecard_runs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE pilot_scorecard_runs ADD COLUMN IF NOT EXISTS run_code VARCHAR(50);
ALTER TABLE pilot_scorecard_runs ADD COLUMN IF NOT EXISTS score_pct FLOAT DEFAULT 0;
ALTER TABLE pilot_scorecard_runs ADD COLUMN IF NOT EXISTS metrics_json TEXT;
ALTER TABLE pilot_scorecard_runs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_pilot_scorecard_runs_run_code ON pilot_scorecard_runs (run_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_pilot_scorecard_runs_run_code'
  ) THEN
    ALTER TABLE pilot_scorecard_runs
      ADD CONSTRAINT uq_pilot_scorecard_runs_run_code UNIQUE (run_code);
  END IF;
END $$;


-- ===== pilot_training_guides =====
CREATE TABLE IF NOT EXISTS pilot_training_guides (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE pilot_training_guides ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE pilot_training_guides ADD COLUMN IF NOT EXISTS guide_code VARCHAR(50);
ALTER TABLE pilot_training_guides ADD COLUMN IF NOT EXISTS audience VARCHAR(50);
ALTER TABLE pilot_training_guides ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE pilot_training_guides ADD COLUMN IF NOT EXISTS body TEXT;
ALTER TABLE pilot_training_guides ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0;
ALTER TABLE pilot_training_guides ADD COLUMN IF NOT EXISTS published BOOLEAN DEFAULT TRUE;
ALTER TABLE pilot_training_guides ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_pilot_training_guides_guide_code ON pilot_training_guides (guide_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_pilot_training_guides_guide_code'
  ) THEN
    ALTER TABLE pilot_training_guides
      ADD CONSTRAINT uq_pilot_training_guides_guide_code UNIQUE (guide_code);
  END IF;
END $$;


-- ===== pilot_wizard_sessions =====
CREATE TABLE IF NOT EXISTS pilot_wizard_sessions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE pilot_wizard_sessions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE pilot_wizard_sessions ADD COLUMN IF NOT EXISTS organization_name VARCHAR(255);
ALTER TABLE pilot_wizard_sessions ADD COLUMN IF NOT EXISTS current_step VARCHAR(50) DEFAULT 'organization';
ALTER TABLE pilot_wizard_sessions ADD COLUMN IF NOT EXISTS checklist_json TEXT;
ALTER TABLE pilot_wizard_sessions ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'in_progress';
ALTER TABLE pilot_wizard_sessions ADD COLUMN IF NOT EXISTS created_by VARCHAR(255);
ALTER TABLE pilot_wizard_sessions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE pilot_wizard_sessions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== portal_favorites =====
CREATE TABLE IF NOT EXISTS portal_favorites (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE portal_favorites ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE portal_favorites ADD COLUMN IF NOT EXISTS owner_type VARCHAR(20);
ALTER TABLE portal_favorites ADD COLUMN IF NOT EXISTS owner_id VARCHAR(50);
ALTER TABLE portal_favorites ADD COLUMN IF NOT EXISTS favorite_type VARCHAR(30);
ALTER TABLE portal_favorites ADD COLUMN IF NOT EXISTS favorite_id VARCHAR(50);
ALTER TABLE portal_favorites ADD COLUMN IF NOT EXISTS label VARCHAR(255);
ALTER TABLE portal_favorites ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_portal_favorites_owner_id ON portal_favorites (owner_id);



-- ===== portal_notifications =====
CREATE TABLE IF NOT EXISTS portal_notifications (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE portal_notifications ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE portal_notifications ADD COLUMN IF NOT EXISTS recipient_type VARCHAR(30);
ALTER TABLE portal_notifications ADD COLUMN IF NOT EXISTS recipient_id VARCHAR(50);
ALTER TABLE portal_notifications ADD COLUMN IF NOT EXISTS event_type VARCHAR(50);
ALTER TABLE portal_notifications ADD COLUMN IF NOT EXISTS channel VARCHAR(30) DEFAULT 'IN_APP';
ALTER TABLE portal_notifications ADD COLUMN IF NOT EXISTS title VARCHAR(255);
ALTER TABLE portal_notifications ADD COLUMN IF NOT EXISTS body TEXT;
ALTER TABLE portal_notifications ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'unread';
ALTER TABLE portal_notifications ADD COLUMN IF NOT EXISTS payload_json TEXT;
ALTER TABLE portal_notifications ADD COLUMN IF NOT EXISTS read_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE portal_notifications ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE portal_notifications ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_portal_notifications_recipient_type ON portal_notifications (recipient_type);
CREATE INDEX IF NOT EXISTS ix_portal_notifications_recipient_id ON portal_notifications (recipient_id);
CREATE INDEX IF NOT EXISTS ix_portal_notifications_status ON portal_notifications (status);



-- ===== portal_qr_tokens =====
CREATE TABLE IF NOT EXISTS portal_qr_tokens (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE portal_qr_tokens ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE portal_qr_tokens ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE portal_qr_tokens ADD COLUMN IF NOT EXISTS verification_token VARCHAR(128);
ALTER TABLE portal_qr_tokens ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE portal_qr_tokens ADD COLUMN IF NOT EXISTS qr_payload VARCHAR(255);
ALTER TABLE portal_qr_tokens ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE portal_qr_tokens ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_portal_qr_tokens_patient_id ON portal_qr_tokens (patient_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_portal_qr_tokens_verification_token ON portal_qr_tokens (verification_token);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_portal_qr_tokens_verification_token'
  ) THEN
    ALTER TABLE portal_qr_tokens
      ADD CONSTRAINT uq_portal_qr_tokens_verification_token UNIQUE (verification_token);
  END IF;
END $$;


-- ===== reception_activity_logs =====
CREATE TABLE IF NOT EXISTS reception_activity_logs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE reception_activity_logs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE reception_activity_logs ADD COLUMN IF NOT EXISTS action VARCHAR(50);
ALTER TABLE reception_activity_logs ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE reception_activity_logs ADD COLUMN IF NOT EXISTS queue_entry_id VARCHAR(36);
ALTER TABLE reception_activity_logs ADD COLUMN IF NOT EXISTS details TEXT;
ALTER TABLE reception_activity_logs ADD COLUMN IF NOT EXISTS actor_email VARCHAR(255);
ALTER TABLE reception_activity_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_reception_activity_logs_action ON reception_activity_logs (action);
CREATE INDEX IF NOT EXISTS ix_reception_activity_logs_patient_id ON reception_activity_logs (patient_id);
CREATE INDEX IF NOT EXISTS ix_reception_activity_logs_queue_entry_id ON reception_activity_logs (queue_entry_id);
CREATE INDEX IF NOT EXISTS ix_reception_activity_logs_created_at ON reception_activity_logs (created_at);



-- ===== reception_queue_entries =====
CREATE TABLE IF NOT EXISTS reception_queue_entries (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS queue_number VARCHAR(30);
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS queue_date DATE;
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS daily_sequence INTEGER;
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS patient_id VARCHAR(50);
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS visit_type VARCHAR(30) DEFAULT 'WALK_IN';
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'WAITING';
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS appointment_id VARCHAR(36);
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS payment_status VARCHAR(30) DEFAULT 'PENDING';
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS workflow_status VARCHAR(30) DEFAULT 'WAITING';
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS checked_in_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS checked_out_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS created_by VARCHAR(255);
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE reception_queue_entries ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_reception_queue_entries_queue_number ON reception_queue_entries (queue_number);
CREATE INDEX IF NOT EXISTS ix_reception_queue_entries_queue_date ON reception_queue_entries (queue_date);
CREATE INDEX IF NOT EXISTS ix_reception_queue_entries_patient_id ON reception_queue_entries (patient_id);
CREATE INDEX IF NOT EXISTS ix_reception_queue_entries_status ON reception_queue_entries (status);
CREATE INDEX IF NOT EXISTS ix_reception_queue_entries_order_id ON reception_queue_entries (order_id);
CREATE INDEX IF NOT EXISTS ix_reception_queue_entries_workflow_status ON reception_queue_entries (workflow_status);


DO $$
BEGIN
  IF to_regclass('public.patients') IS NULL THEN
    RAISE NOTICE 'patients missing — skip FK fk_reception_queue_entries_patient_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_reception_queue_entries_patient_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE reception_queue_entries
    ADD CONSTRAINT fk_reception_queue_entries_patient_id
    FOREIGN KEY (patient_id) REFERENCES patients (patient_code);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_reception_queue_entries_patient_id: %', SQLERRM;
END $$;

-- ===== recollect_requests =====
CREATE TABLE IF NOT EXISTS recollect_requests (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE recollect_requests ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE recollect_requests ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE recollect_requests ADD COLUMN IF NOT EXISTS sample_id VARCHAR(36);
ALTER TABLE recollect_requests ADD COLUMN IF NOT EXISTS reason TEXT;
ALTER TABLE recollect_requests ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE recollect_requests ADD COLUMN IF NOT EXISTS requested_by VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE recollect_requests ADD COLUMN IF NOT EXISTS scheduled_date VARCHAR(20);
ALTER TABLE recollect_requests ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE recollect_requests ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE recollect_requests ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_recollect_requests_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_recollect_requests_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE recollect_requests
    ADD CONSTRAINT fk_recollect_requests_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_recollect_requests_medical_order_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.medical_samples') IS NULL THEN
    RAISE NOTICE 'medical_samples missing — skip FK fk_recollect_requests_sample_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_recollect_requests_sample_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE recollect_requests
    ADD CONSTRAINT fk_recollect_requests_sample_id
    FOREIGN KEY (sample_id) REFERENCES medical_samples (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_recollect_requests_sample_id: %', SQLERRM;
END $$;

-- ===== reference_libraries =====
CREATE TABLE IF NOT EXISTS reference_libraries (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE reference_libraries ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE reference_libraries ADD COLUMN IF NOT EXISTS reference_code VARCHAR(50);
ALTER TABLE reference_libraries ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE reference_libraries ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE reference_libraries ADD COLUMN IF NOT EXISTS low_value FLOAT;
ALTER TABLE reference_libraries ADD COLUMN IF NOT EXISTS high_value FLOAT;
ALTER TABLE reference_libraries ADD COLUMN IF NOT EXISTS unit VARCHAR(50);
ALTER TABLE reference_libraries ADD COLUMN IF NOT EXISTS source_pack VARCHAR(50);
ALTER TABLE reference_libraries ADD COLUMN IF NOT EXISTS version VARCHAR(20) DEFAULT '1.0';
ALTER TABLE reference_libraries ADD COLUMN IF NOT EXISTS citation_json TEXT DEFAULT '{}';
ALTER TABLE reference_libraries ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE reference_libraries ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_reference_libraries_reference_code ON reference_libraries (reference_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_reference_libraries_reference_code'
  ) THEN
    ALTER TABLE reference_libraries
      ADD CONSTRAINT uq_reference_libraries_reference_code UNIQUE (reference_code);
  END IF;
END $$;


-- ===== reference_ranges =====
CREATE TABLE IF NOT EXISTS reference_ranges (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE reference_ranges ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE reference_ranges ADD COLUMN IF NOT EXISTS test_code VARCHAR(50);
ALTER TABLE reference_ranges ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE reference_ranges ADD COLUMN IF NOT EXISTS sex VARCHAR(10) DEFAULT 'ALL';
ALTER TABLE reference_ranges ADD COLUMN IF NOT EXISTS age_min INTEGER DEFAULT 0;
ALTER TABLE reference_ranges ADD COLUMN IF NOT EXISTS age_max INTEGER DEFAULT 120;
ALTER TABLE reference_ranges ADD COLUMN IF NOT EXISTS unit VARCHAR(50);
ALTER TABLE reference_ranges ADD COLUMN IF NOT EXISTS low_value FLOAT;
ALTER TABLE reference_ranges ADD COLUMN IF NOT EXISTS high_value FLOAT;
ALTER TABLE reference_ranges ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'ACTIVE';
ALTER TABLE reference_ranges ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== refresh_token_records =====
CREATE TABLE IF NOT EXISTS refresh_token_records (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE refresh_token_records ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE refresh_token_records ADD COLUMN IF NOT EXISTS user_id VARCHAR(36);
ALTER TABLE refresh_token_records ADD COLUMN IF NOT EXISTS jti VARCHAR(64);
ALTER TABLE refresh_token_records ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE refresh_token_records ADD COLUMN IF NOT EXISTS revoked BOOLEAN DEFAULT FALSE;
ALTER TABLE refresh_token_records ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_refresh_token_records_jti ON refresh_token_records (jti);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_refresh_token_records_jti'
  ) THEN
    ALTER TABLE refresh_token_records
      ADD CONSTRAINT uq_refresh_token_records_jti UNIQUE (jti);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.users') IS NULL THEN
    RAISE NOTICE 'users missing — skip FK fk_refresh_token_records_user_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_refresh_token_records_user_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE refresh_token_records
    ADD CONSTRAINT fk_refresh_token_records_user_id
    FOREIGN KEY (user_id) REFERENCES users (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_refresh_token_records_user_id: %', SQLERRM;
END $$;

-- ===== refund_records =====
CREATE TABLE IF NOT EXISTS refund_records (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE refund_records ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE refund_records ADD COLUMN IF NOT EXISTS refund_code VARCHAR(50);
ALTER TABLE refund_records ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE refund_records ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE refund_records ADD COLUMN IF NOT EXISTS payment_record_id VARCHAR(36);
ALTER TABLE refund_records ADD COLUMN IF NOT EXISTS amount FLOAT DEFAULT 0;
ALTER TABLE refund_records ADD COLUMN IF NOT EXISTS reason TEXT;
ALTER TABLE refund_records ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE refund_records ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE refund_records ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_refund_records_refund_code ON refund_records (refund_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_refund_records_refund_code'
  ) THEN
    ALTER TABLE refund_records
      ADD CONSTRAINT uq_refund_records_refund_code UNIQUE (refund_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_refund_records_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_refund_records_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE refund_records
    ADD CONSTRAINT fk_refund_records_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_refund_records_medical_order_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.invoices') IS NULL THEN
    RAISE NOTICE 'invoices missing — skip FK fk_refund_records_invoice_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_refund_records_invoice_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE refund_records
    ADD CONSTRAINT fk_refund_records_invoice_id
    FOREIGN KEY (invoice_id) REFERENCES invoices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_refund_records_invoice_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.payment_records') IS NULL THEN
    RAISE NOTICE 'payment_records missing — skip FK fk_refund_records_payment_record_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_refund_records_payment_record_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE refund_records
    ADD CONSTRAINT fk_refund_records_payment_record_id
    FOREIGN KEY (payment_record_id) REFERENCES payment_records (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_refund_records_payment_record_id: %', SQLERRM;
END $$;

-- ===== report_definitions =====
CREATE TABLE IF NOT EXISTS report_definitions (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE report_definitions ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE report_definitions ADD COLUMN IF NOT EXISTS definition_code VARCHAR(50);
ALTER TABLE report_definitions ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE report_definitions ADD COLUMN IF NOT EXISTS report_type VARCHAR(50);
ALTER TABLE report_definitions ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE report_definitions ADD COLUMN IF NOT EXISTS default_format VARCHAR(20) DEFAULT 'JSON';
ALTER TABLE report_definitions ADD COLUMN IF NOT EXISTS config_json TEXT DEFAULT '{}';
ALTER TABLE report_definitions ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE report_definitions ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_report_definitions_definition_code ON report_definitions (definition_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_report_definitions_definition_code'
  ) THEN
    ALTER TABLE report_definitions
      ADD CONSTRAINT uq_report_definitions_definition_code UNIQUE (definition_code);
  END IF;
END $$;


-- ===== report_digital_signatures =====
CREATE TABLE IF NOT EXISTS report_digital_signatures (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE report_digital_signatures ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE report_digital_signatures ADD COLUMN IF NOT EXISTS report_id VARCHAR(36);
ALTER TABLE report_digital_signatures ADD COLUMN IF NOT EXISTS signer_id VARCHAR(36);
ALTER TABLE report_digital_signatures ADD COLUMN IF NOT EXISTS signer_name VARCHAR(255);
ALTER TABLE report_digital_signatures ADD COLUMN IF NOT EXISTS signer_role VARCHAR(50);
ALTER TABLE report_digital_signatures ADD COLUMN IF NOT EXISTS signed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE report_digital_signatures ADD COLUMN IF NOT EXISTS signature_hash VARCHAR(128);
ALTER TABLE report_digital_signatures ADD COLUMN IF NOT EXISTS report_hash VARCHAR(128);
ALTER TABLE report_digital_signatures ADD COLUMN IF NOT EXISTS signature_method VARCHAR(50) DEFAULT 'INTERNAL_APPROVAL';
ALTER TABLE report_digital_signatures ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_report_digital_signatures_report_id ON report_digital_signatures (report_id);


DO $$
BEGIN
  IF to_regclass('public.clinical_reports') IS NULL THEN
    RAISE NOTICE 'clinical_reports missing — skip FK fk_report_digital_signatures_report_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_report_digital_signatures_report_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE report_digital_signatures
    ADD CONSTRAINT fk_report_digital_signatures_report_id
    FOREIGN KEY (report_id) REFERENCES clinical_reports (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_report_digital_signatures_report_id: %', SQLERRM;
END $$;

-- ===== report_jobs =====
CREATE TABLE IF NOT EXISTS report_jobs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS job_code VARCHAR(50);
ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS definition_id VARCHAR(36);
ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS report_type VARCHAR(50);
ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS output_format VARCHAR(20) DEFAULT 'JSON';
ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS file_path VARCHAR(500);
ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS payload_json TEXT;
ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS requested_by VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE report_jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_report_jobs_job_code ON report_jobs (job_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_report_jobs_job_code'
  ) THEN
    ALTER TABLE report_jobs
      ADD CONSTRAINT uq_report_jobs_job_code UNIQUE (job_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.report_definitions') IS NULL THEN
    RAISE NOTICE 'report_definitions missing — skip FK fk_report_jobs_definition_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_report_jobs_definition_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE report_jobs
    ADD CONSTRAINT fk_report_jobs_definition_id
    FOREIGN KEY (definition_id) REFERENCES report_definitions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_report_jobs_definition_id: %', SQLERRM;
END $$;

-- ===== report_notification_events =====
CREATE TABLE IF NOT EXISTS report_notification_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE report_notification_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE report_notification_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(50);
ALTER TABLE report_notification_events ADD COLUMN IF NOT EXISTS recipient_type VARCHAR(30);
ALTER TABLE report_notification_events ADD COLUMN IF NOT EXISTS recipient_id VARCHAR(50);
ALTER TABLE report_notification_events ADD COLUMN IF NOT EXISTS channel VARCHAR(30);
ALTER TABLE report_notification_events ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'pending';
ALTER TABLE report_notification_events ADD COLUMN IF NOT EXISTS payload_json TEXT;
ALTER TABLE report_notification_events ADD COLUMN IF NOT EXISTS report_id VARCHAR(36);
ALTER TABLE report_notification_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== report_schedules =====
CREATE TABLE IF NOT EXISTS report_schedules (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS schedule_code VARCHAR(50);
ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS definition_id VARCHAR(36);
ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS report_type VARCHAR(50);
ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS cadence VARCHAR(20);
ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS output_format VARCHAR(20) DEFAULT 'PDF';
ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS recipient_emails TEXT;
ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS next_run_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS last_run_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS config_json TEXT DEFAULT '{}';
ALTER TABLE report_schedules ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_report_schedules_schedule_code ON report_schedules (schedule_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_report_schedules_schedule_code'
  ) THEN
    ALTER TABLE report_schedules
      ADD CONSTRAINT uq_report_schedules_schedule_code UNIQUE (schedule_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.report_definitions') IS NULL THEN
    RAISE NOTICE 'report_definitions missing — skip FK fk_report_schedules_definition_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_report_schedules_definition_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE report_schedules
    ADD CONSTRAINT fk_report_schedules_definition_id
    FOREIGN KEY (definition_id) REFERENCES report_definitions (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_report_schedules_definition_id: %', SQLERRM;
END $$;

-- ===== report_snapshots =====
CREATE TABLE IF NOT EXISTS report_snapshots (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE report_snapshots ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE report_snapshots ADD COLUMN IF NOT EXISTS snapshot_code VARCHAR(50);
ALTER TABLE report_snapshots ADD COLUMN IF NOT EXISTS report_type VARCHAR(50);
ALTER TABLE report_snapshots ADD COLUMN IF NOT EXISTS period_start TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE report_snapshots ADD COLUMN IF NOT EXISTS period_end TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE report_snapshots ADD COLUMN IF NOT EXISTS payload_json TEXT;
ALTER TABLE report_snapshots ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_report_snapshots_snapshot_code ON report_snapshots (snapshot_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_report_snapshots_snapshot_code'
  ) THEN
    ALTER TABLE report_snapshots
      ADD CONSTRAINT uq_report_snapshots_snapshot_code UNIQUE (snapshot_code);
  END IF;
END $$;


-- ===== result_attachments =====
CREATE TABLE IF NOT EXISTS result_attachments (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE result_attachments ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE result_attachments ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE result_attachments ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);
ALTER TABLE result_attachments ADD COLUMN IF NOT EXISTS file_path TEXT;
ALTER TABLE result_attachments ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100);
ALTER TABLE result_attachments ADD COLUMN IF NOT EXISTS attachment_type VARCHAR(20) DEFAULT 'PDF';
ALTER TABLE result_attachments ADD COLUMN IF NOT EXISTS uploaded_by VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE result_attachments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.lab_results') IS NULL THEN
    RAISE NOTICE 'lab_results missing — skip FK fk_result_attachments_lab_result_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_result_attachments_lab_result_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE result_attachments
    ADD CONSTRAINT fk_result_attachments_lab_result_id
    FOREIGN KEY (lab_result_id) REFERENCES lab_results (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_result_attachments_lab_result_id: %', SQLERRM;
END $$;

-- ===== result_files =====
CREATE TABLE IF NOT EXISTS result_files (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE result_files ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE result_files ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE result_files ADD COLUMN IF NOT EXISTS file_name VARCHAR(255);
ALTER TABLE result_files ADD COLUMN IF NOT EXISTS file_path TEXT;
ALTER TABLE result_files ADD COLUMN IF NOT EXISTS uploaded_by VARCHAR(36);
ALTER TABLE result_files ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== result_releases =====
CREATE TABLE IF NOT EXISTS result_releases (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE result_releases ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE result_releases ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE result_releases ADD COLUMN IF NOT EXISTS release_code VARCHAR(50);
ALTER TABLE result_releases ADD COLUMN IF NOT EXISTS released_by VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE result_releases ADD COLUMN IF NOT EXISTS release_channel VARCHAR(50) DEFAULT 'PORTAL';
ALTER TABLE result_releases ADD COLUMN IF NOT EXISTS payload_json TEXT;
ALTER TABLE result_releases ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 1;
ALTER TABLE result_releases ADD COLUMN IF NOT EXISTS released_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_result_releases_release_code ON result_releases (release_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_result_releases_release_code'
  ) THEN
    ALTER TABLE result_releases
      ADD CONSTRAINT uq_result_releases_release_code UNIQUE (release_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.lab_results') IS NULL THEN
    RAISE NOTICE 'lab_results missing — skip FK fk_result_releases_lab_result_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_result_releases_lab_result_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE result_releases
    ADD CONSTRAINT fk_result_releases_lab_result_id
    FOREIGN KEY (lab_result_id) REFERENCES lab_results (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_result_releases_lab_result_id: %', SQLERRM;
END $$;

-- ===== result_reviews =====
CREATE TABLE IF NOT EXISTS result_reviews (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE result_reviews ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE result_reviews ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE result_reviews ADD COLUMN IF NOT EXISTS reviewer_email VARCHAR(255);
ALTER TABLE result_reviews ADD COLUMN IF NOT EXISTS review_status VARCHAR(50) DEFAULT 'SUBMITTED';
ALTER TABLE result_reviews ADD COLUMN IF NOT EXISTS comments TEXT;
ALTER TABLE result_reviews ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.lab_results') IS NULL THEN
    RAISE NOTICE 'lab_results missing — skip FK fk_result_reviews_lab_result_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_result_reviews_lab_result_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE result_reviews
    ADD CONSTRAINT fk_result_reviews_lab_result_id
    FOREIGN KEY (lab_result_id) REFERENCES lab_results (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_result_reviews_lab_result_id: %', SQLERRM;
END $$;

-- ===== result_timelines =====
CREATE TABLE IF NOT EXISTS result_timelines (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE result_timelines ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE result_timelines ADD COLUMN IF NOT EXISTS lab_result_id VARCHAR(36);
ALTER TABLE result_timelines ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE result_timelines ADD COLUMN IF NOT EXISTS from_status VARCHAR(50);
ALTER TABLE result_timelines ADD COLUMN IF NOT EXISTS to_status VARCHAR(50);
ALTER TABLE result_timelines ADD COLUMN IF NOT EXISTS message TEXT;
ALTER TABLE result_timelines ADD COLUMN IF NOT EXISTS actor_email VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE result_timelines ADD COLUMN IF NOT EXISTS metadata_json TEXT;
ALTER TABLE result_timelines ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.lab_results') IS NULL THEN
    RAISE NOTICE 'lab_results missing — skip FK fk_result_timelines_lab_result_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_result_timelines_lab_result_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE result_timelines
    ADD CONSTRAINT fk_result_timelines_lab_result_id
    FOREIGN KEY (lab_result_id) REFERENCES lab_results (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_result_timelines_lab_result_id: %', SQLERRM;
END $$;

-- ===== revenue_analytics =====
CREATE TABLE IF NOT EXISTS revenue_analytics (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE revenue_analytics ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE revenue_analytics ADD COLUMN IF NOT EXISTS analytics_code VARCHAR(50);
ALTER TABLE revenue_analytics ADD COLUMN IF NOT EXISTS period_start TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE revenue_analytics ADD COLUMN IF NOT EXISTS period_end TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE revenue_analytics ADD COLUMN IF NOT EXISTS gross_revenue FLOAT DEFAULT 0;
ALTER TABLE revenue_analytics ADD COLUMN IF NOT EXISTS net_revenue FLOAT DEFAULT 0;
ALTER TABLE revenue_analytics ADD COLUMN IF NOT EXISTS invoice_count INTEGER DEFAULT 0;
ALTER TABLE revenue_analytics ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE revenue_analytics ADD COLUMN IF NOT EXISTS clinic_id VARCHAR(36);
ALTER TABLE revenue_analytics ADD COLUMN IF NOT EXISTS metrics_json TEXT DEFAULT '{}';
ALTER TABLE revenue_analytics ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_revenue_analytics_analytics_code ON revenue_analytics (analytics_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_revenue_analytics_analytics_code'
  ) THEN
    ALTER TABLE revenue_analytics
      ADD CONSTRAINT uq_revenue_analytics_analytics_code UNIQUE (analytics_code);
  END IF;
END $$;


-- ===== sample_collections =====
CREATE TABLE IF NOT EXISTS sample_collections (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS marketplace_booking_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collection_mode VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS sample_tracking_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collector_name VARCHAR(255);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collected_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS specimen_type VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS barcode_value VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS expected_barcode VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collection_location VARCHAR(255);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS location_city VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS quality_status VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS partner_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS recollect_of_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS patient_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS order_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS picked_up_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS dispatched_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS handoff_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS arrived_at_lab TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS vehicle_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS driver_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS transport_box_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS distance_km FLOAT;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS eta_minutes INTEGER;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS temperature_c FLOAT;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS iot_device_id VARCHAR(36);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_address VARCHAR(500);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_city VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_province VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_district VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_ward VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS contact_person VARCHAR(255);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS requested_date VARCHAR(20);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS requested_time_window VARCHAR(100);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_latitude VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS pickup_longitude VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS collection_request_note TEXT;
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS clinic_name VARCHAR(255);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS priority VARCHAR(50);
ALTER TABLE sample_collections ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.marketplace_bookings') IS NULL THEN
    RAISE NOTICE 'marketplace_bookings missing — skip FK fk_sample_collections_marketplace_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_sample_collections_marketplace_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE sample_collections
    ADD CONSTRAINT fk_sample_collections_marketplace_booking_id
    FOREIGN KEY (marketplace_booking_id) REFERENCES marketplace_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_sample_collections_marketplace_booking_id: %', SQLERRM;
END $$;

-- ===== sample_events =====
CREATE TABLE IF NOT EXISTS sample_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE sample_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE sample_events ADD COLUMN IF NOT EXISTS sample_tracking_id VARCHAR(36);
ALTER TABLE sample_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE sample_events ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE sample_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== sample_incidents =====
CREATE TABLE IF NOT EXISTS sample_incidents (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE sample_incidents ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE sample_incidents ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE sample_incidents ADD COLUMN IF NOT EXISTS sample_id VARCHAR(36);
ALTER TABLE sample_incidents ADD COLUMN IF NOT EXISTS incident_type VARCHAR(100);
ALTER TABLE sample_incidents ADD COLUMN IF NOT EXISTS severity VARCHAR(50) DEFAULT 'MEDIUM';
ALTER TABLE sample_incidents ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'OPEN';
ALTER TABLE sample_incidents ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE sample_incidents ADD COLUMN IF NOT EXISTS resolution_note TEXT;
ALTER TABLE sample_incidents ADD COLUMN IF NOT EXISTS reported_by VARCHAR(255) DEFAULT 'SYSTEM';
ALTER TABLE sample_incidents ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE sample_incidents ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE sample_incidents ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.medical_samples') IS NULL THEN
    RAISE NOTICE 'medical_samples missing — skip FK fk_sample_incidents_sample_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_sample_incidents_sample_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE sample_incidents
    ADD CONSTRAINT fk_sample_incidents_sample_id
    FOREIGN KEY (sample_id) REFERENCES medical_samples (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_sample_incidents_sample_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_sample_incidents_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_sample_incidents_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE sample_incidents
    ADD CONSTRAINT fk_sample_incidents_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_sample_incidents_medical_order_id: %', SQLERRM;
END $$;

-- ===== sample_labels =====
CREATE TABLE IF NOT EXISTS sample_labels (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE sample_labels ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE sample_labels ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE sample_labels ADD COLUMN IF NOT EXISTS sample_id VARCHAR(36);
ALTER TABLE sample_labels ADD COLUMN IF NOT EXISTS label_code VARCHAR(100);
ALTER TABLE sample_labels ADD COLUMN IF NOT EXISTS template_name VARCHAR(100) DEFAULT 'STANDARD';
ALTER TABLE sample_labels ADD COLUMN IF NOT EXISTS print_payload TEXT;
ALTER TABLE sample_labels ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE sample_labels ADD COLUMN IF NOT EXISTS printed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE sample_labels ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_sample_labels_label_code ON sample_labels (label_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_sample_labels_label_code'
  ) THEN
    ALTER TABLE sample_labels
      ADD CONSTRAINT uq_sample_labels_label_code UNIQUE (label_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_sample_labels_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_sample_labels_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE sample_labels
    ADD CONSTRAINT fk_sample_labels_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_sample_labels_medical_order_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.medical_samples') IS NULL THEN
    RAISE NOTICE 'medical_samples missing — skip FK fk_sample_labels_sample_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_sample_labels_sample_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE sample_labels
    ADD CONSTRAINT fk_sample_labels_sample_id
    FOREIGN KEY (sample_id) REFERENCES medical_samples (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_sample_labels_sample_id: %', SQLERRM;
END $$;

-- ===== sample_trackings =====
CREATE TABLE IF NOT EXISTS sample_trackings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS sample_code VARCHAR(50);
ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS home_collection_id VARCHAR(36);
ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS marketplace_booking_id VARCHAR(36);
ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS medical_sample_id VARCHAR(36);
ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS transport_box_id VARCHAR(36);
ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS latitude VARCHAR(50);
ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS longitude VARCHAR(50);
ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'CHECKED_IN';
ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE sample_trackings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_sample_trackings_sample_code ON sample_trackings (sample_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_sample_trackings_sample_code'
  ) THEN
    ALTER TABLE sample_trackings
      ADD CONSTRAINT uq_sample_trackings_sample_code UNIQUE (sample_code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.medical_samples') IS NULL THEN
    RAISE NOTICE 'medical_samples missing — skip FK fk_sample_trackings_medical_sample_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_sample_trackings_medical_sample_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE sample_trackings
    ADD CONSTRAINT fk_sample_trackings_medical_sample_id
    FOREIGN KEY (medical_sample_id) REFERENCES medical_samples (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_sample_trackings_medical_sample_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_sample_trackings_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_sample_trackings_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE sample_trackings
    ADD CONSTRAINT fk_sample_trackings_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_sample_trackings_medical_order_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.marketplace_bookings') IS NULL THEN
    RAISE NOTICE 'marketplace_bookings missing — skip FK fk_sample_trackings_marketplace_booking_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_sample_trackings_marketplace_booking_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE sample_trackings
    ADD CONSTRAINT fk_sample_trackings_marketplace_booking_id
    FOREIGN KEY (marketplace_booking_id) REFERENCES marketplace_bookings (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_sample_trackings_marketplace_booking_id: %', SQLERRM;
END $$;

-- ===== scheduling_calendars =====
CREATE TABLE IF NOT EXISTS scheduling_calendars (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE scheduling_calendars ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE scheduling_calendars ADD COLUMN IF NOT EXISTS owner_type VARCHAR(50);
ALTER TABLE scheduling_calendars ADD COLUMN IF NOT EXISTS owner_id VARCHAR(36);
ALTER TABLE scheduling_calendars ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE scheduling_calendars ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'Asia/Ho_Chi_Minh';
ALTER TABLE scheduling_calendars ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE scheduling_calendars ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE scheduling_calendars ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_scheduling_calendar_owner'
  ) THEN
    ALTER TABLE scheduling_calendars
      ADD CONSTRAINT uq_scheduling_calendar_owner UNIQUE (owner_type, owner_id);
  END IF;
END $$;


-- ===== scheduling_slots =====
CREATE TABLE IF NOT EXISTS scheduling_slots (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE scheduling_slots ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE scheduling_slots ADD COLUMN IF NOT EXISTS calendar_id VARCHAR(36);
ALTER TABLE scheduling_slots ADD COLUMN IF NOT EXISTS slot_date VARCHAR(20);
ALTER TABLE scheduling_slots ADD COLUMN IF NOT EXISTS start_time VARCHAR(10);
ALTER TABLE scheduling_slots ADD COLUMN IF NOT EXISTS end_time VARCHAR(10);
ALTER TABLE scheduling_slots ADD COLUMN IF NOT EXISTS slot_type VARCHAR(50) DEFAULT 'COLLECTION';
ALTER TABLE scheduling_slots ADD COLUMN IF NOT EXISTS capacity INTEGER DEFAULT 1;
ALTER TABLE scheduling_slots ADD COLUMN IF NOT EXISTS booked_count INTEGER DEFAULT 0;
ALTER TABLE scheduling_slots ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'AVAILABLE';
ALTER TABLE scheduling_slots ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE scheduling_slots ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;


DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_scheduling_slot_window'
  ) THEN
    ALTER TABLE scheduling_slots
      ADD CONSTRAINT uq_scheduling_slot_window UNIQUE (calendar_id, slot_date, start_time, end_time, slot_type);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.scheduling_calendars') IS NULL THEN
    RAISE NOTICE 'scheduling_calendars missing — skip FK fk_scheduling_slots_calendar_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_scheduling_slots_calendar_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE scheduling_slots
    ADD CONSTRAINT fk_scheduling_slots_calendar_id
    FOREIGN KEY (calendar_id) REFERENCES scheduling_calendars (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_scheduling_slots_calendar_id: %', SQLERRM;
END $$;

-- ===== service_package_items =====
CREATE TABLE IF NOT EXISTS service_package_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE service_package_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE service_package_items ADD COLUMN IF NOT EXISTS package_id VARCHAR(36);
ALTER TABLE service_package_items ADD COLUMN IF NOT EXISTS diagnostic_service_id VARCHAR(36);
ALTER TABLE service_package_items ADD COLUMN IF NOT EXISTS quantity INTEGER DEFAULT 1;
ALTER TABLE service_package_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.diagnostic_services') IS NULL THEN
    RAISE NOTICE 'diagnostic_services missing — skip FK fk_service_package_items_diagnostic_service_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_service_package_items_diagnostic_service_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE service_package_items
    ADD CONSTRAINT fk_service_package_items_diagnostic_service_id
    FOREIGN KEY (diagnostic_service_id) REFERENCES diagnostic_services (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_service_package_items_diagnostic_service_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.service_packages') IS NULL THEN
    RAISE NOTICE 'service_packages missing — skip FK fk_service_package_items_package_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_service_package_items_package_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE service_package_items
    ADD CONSTRAINT fk_service_package_items_package_id
    FOREIGN KEY (package_id) REFERENCES service_packages (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_service_package_items_package_id: %', SQLERRM;
END $$;

-- ===== service_packages =====
CREATE TABLE IF NOT EXISTS service_packages (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE service_packages ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE service_packages ADD COLUMN IF NOT EXISTS package_code VARCHAR(50);
ALTER TABLE service_packages ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE service_packages ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE service_packages ADD COLUMN IF NOT EXISTS target_condition VARCHAR(255);
ALTER TABLE service_packages ADD COLUMN IF NOT EXISTS base_price FLOAT DEFAULT 0;
ALTER TABLE service_packages ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE service_packages ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE service_packages ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_service_packages_package_code ON service_packages (package_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_service_packages_package_code'
  ) THEN
    ALTER TABLE service_packages
      ADD CONSTRAINT uq_service_packages_package_code UNIQUE (package_code);
  END IF;
END $$;


-- ===== settlement_items =====
CREATE TABLE IF NOT EXISTS settlement_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE settlement_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE settlement_items ADD COLUMN IF NOT EXISTS settlement_id VARCHAR(36);
ALTER TABLE settlement_items ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE settlement_items ADD COLUMN IF NOT EXISTS medical_order_id VARCHAR(36);
ALTER TABLE settlement_items ADD COLUMN IF NOT EXISTS description VARCHAR(255);
ALTER TABLE settlement_items ADD COLUMN IF NOT EXISTS gross_amount FLOAT DEFAULT 0;
ALTER TABLE settlement_items ADD COLUMN IF NOT EXISTS commission_amount FLOAT DEFAULT 0;
ALTER TABLE settlement_items ADD COLUMN IF NOT EXISTS net_amount FLOAT DEFAULT 0;
ALTER TABLE settlement_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.medical_orders') IS NULL THEN
    RAISE NOTICE 'medical_orders missing — skip FK fk_settlement_items_medical_order_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_settlement_items_medical_order_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE settlement_items
    ADD CONSTRAINT fk_settlement_items_medical_order_id
    FOREIGN KEY (medical_order_id) REFERENCES medical_orders (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_settlement_items_medical_order_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.invoices') IS NULL THEN
    RAISE NOTICE 'invoices missing — skip FK fk_settlement_items_invoice_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_settlement_items_invoice_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE settlement_items
    ADD CONSTRAINT fk_settlement_items_invoice_id
    FOREIGN KEY (invoice_id) REFERENCES invoices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_settlement_items_invoice_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.partner_settlements') IS NULL THEN
    RAISE NOTICE 'partner_settlements missing — skip FK fk_settlement_items_settlement_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_settlement_items_settlement_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE settlement_items
    ADD CONSTRAINT fk_settlement_items_settlement_id
    FOREIGN KEY (settlement_id) REFERENCES partner_settlements (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_settlement_items_settlement_id: %', SQLERRM;
END $$;

-- ===== shipment_items =====
CREATE TABLE IF NOT EXISTS shipment_items (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE shipment_items ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE shipment_items ADD COLUMN IF NOT EXISTS shipment_id VARCHAR(36);
ALTER TABLE shipment_items ADD COLUMN IF NOT EXISTS order_id VARCHAR(36);
ALTER TABLE shipment_items ADD COLUMN IF NOT EXISTS order_item_id VARCHAR(36);
ALTER TABLE shipment_items ADD COLUMN IF NOT EXISTS sample_tracking_id VARCHAR(36);
ALTER TABLE shipment_items ADD COLUMN IF NOT EXISTS sample_code VARCHAR(100);
ALTER TABLE shipment_items ADD COLUMN IF NOT EXISTS tube_type VARCHAR(100);
ALTER TABLE shipment_items ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE shipment_items ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'CREATED';
ALTER TABLE shipment_items ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE shipment_items ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== shipment_timelines =====
CREATE TABLE IF NOT EXISTS shipment_timelines (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE shipment_timelines ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE shipment_timelines ADD COLUMN IF NOT EXISTS shipment_id VARCHAR(36);
ALTER TABLE shipment_timelines ADD COLUMN IF NOT EXISTS event_type VARCHAR(100);
ALTER TABLE shipment_timelines ADD COLUMN IF NOT EXISTS note TEXT;
ALTER TABLE shipment_timelines ADD COLUMN IF NOT EXISTS actor VARCHAR(255);
ALTER TABLE shipment_timelines ADD COLUMN IF NOT EXISTS gps_location VARCHAR(255);
ALTER TABLE shipment_timelines ADD COLUMN IF NOT EXISTS temperature VARCHAR(50);
ALTER TABLE shipment_timelines ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== shipments =====
CREATE TABLE IF NOT EXISTS shipments (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE shipments ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS shipment_code VARCHAR(100);
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS collector_id VARCHAR(36);
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS transport_box_id VARCHAR(36);
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS lab_name VARCHAR(255);
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'CREATED';
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS sample_count INTEGER DEFAULT 0;
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS temperature VARCHAR(50);
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS gps_location VARCHAR(255);
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS departed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS arrived_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS received_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS received_by VARCHAR(255);
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS receiver_note TEXT;
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE shipments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_shipments_shipment_code ON shipments (shipment_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_shipments_shipment_code'
  ) THEN
    ALTER TABLE shipments
      ADD CONSTRAINT uq_shipments_shipment_code UNIQUE (shipment_code);
  END IF;
END $$;


-- ===== shock_events =====
CREATE TABLE IF NOT EXISTS shock_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE shock_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE shock_events ADD COLUMN IF NOT EXISTS device_id VARCHAR(36);
ALTER TABLE shock_events ADD COLUMN IF NOT EXISTS g_force FLOAT;
ALTER TABLE shock_events ADD COLUMN IF NOT EXISTS recorded_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.iot_devices') IS NULL THEN
    RAISE NOTICE 'iot_devices missing — skip FK fk_shock_events_device_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_shock_events_device_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE shock_events
    ADD CONSTRAINT fk_shock_events_device_id
    FOREIGN KEY (device_id) REFERENCES iot_devices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_shock_events_device_id: %', SQLERRM;
END $$;

-- ===== standard_code_systems =====
CREATE TABLE IF NOT EXISTS standard_code_systems (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE standard_code_systems ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE standard_code_systems ADD COLUMN IF NOT EXISTS system_code VARCHAR(50);
ALTER TABLE standard_code_systems ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE standard_code_systems ADD COLUMN IF NOT EXISTS version VARCHAR(50);
ALTER TABLE standard_code_systems ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE standard_code_systems ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_standard_code_systems_system_code ON standard_code_systems (system_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_standard_code_systems_system_code'
  ) THEN
    ALTER TABLE standard_code_systems
      ADD CONSTRAINT uq_standard_code_systems_system_code UNIQUE (system_code);
  END IF;
END $$;


-- ===== standard_codes =====
CREATE TABLE IF NOT EXISTS standard_codes (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE standard_codes ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE standard_codes ADD COLUMN IF NOT EXISTS system_id VARCHAR(36);
ALTER TABLE standard_codes ADD COLUMN IF NOT EXISTS code VARCHAR(100);
ALTER TABLE standard_codes ADD COLUMN IF NOT EXISTS display VARCHAR(500);
ALTER TABLE standard_codes ADD COLUMN IF NOT EXISTS category VARCHAR(100);
ALTER TABLE standard_codes ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE standard_codes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_standard_codes_code ON standard_codes (code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_standard_code_system_code'
  ) THEN
    ALTER TABLE standard_codes
      ADD CONSTRAINT uq_standard_code_system_code UNIQUE (system_id, code);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.standard_code_systems') IS NULL THEN
    RAISE NOTICE 'standard_code_systems missing — skip FK fk_standard_codes_system_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_standard_codes_system_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE standard_codes
    ADD CONSTRAINT fk_standard_codes_system_id
    FOREIGN KEY (system_id) REFERENCES standard_code_systems (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_standard_codes_system_id: %', SQLERRM;
END $$;

-- ===== standard_import_batches =====
CREATE TABLE IF NOT EXISTS standard_import_batches (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE standard_import_batches ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE standard_import_batches ADD COLUMN IF NOT EXISTS batch_code VARCHAR(50);
ALTER TABLE standard_import_batches ADD COLUMN IF NOT EXISTS system_code VARCHAR(50);
ALTER TABLE standard_import_batches ADD COLUMN IF NOT EXISTS record_count INTEGER DEFAULT 0;
ALTER TABLE standard_import_batches ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'COMPLETED';
ALTER TABLE standard_import_batches ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_standard_import_batches_batch_code ON standard_import_batches (batch_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_standard_import_batches_batch_code'
  ) THEN
    ALTER TABLE standard_import_batches
      ADD CONSTRAINT uq_standard_import_batches_batch_code UNIQUE (batch_code);
  END IF;
END $$;


-- ===== standard_mappings =====
CREATE TABLE IF NOT EXISTS standard_mappings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE standard_mappings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE standard_mappings ADD COLUMN IF NOT EXISTS mapping_code VARCHAR(50);
ALTER TABLE standard_mappings ADD COLUMN IF NOT EXISTS source_type VARCHAR(100);
ALTER TABLE standard_mappings ADD COLUMN IF NOT EXISTS source_code VARCHAR(100);
ALTER TABLE standard_mappings ADD COLUMN IF NOT EXISTS target_system VARCHAR(50);
ALTER TABLE standard_mappings ADD COLUMN IF NOT EXISTS target_code VARCHAR(100);
ALTER TABLE standard_mappings ADD COLUMN IF NOT EXISTS target_display VARCHAR(500);
ALTER TABLE standard_mappings ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ACTIVE';
ALTER TABLE standard_mappings ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_standard_mappings_mapping_code ON standard_mappings (mapping_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_standard_mappings_mapping_code'
  ) THEN
    ALTER TABLE standard_mappings
      ADD CONSTRAINT uq_standard_mappings_mapping_code UNIQUE (mapping_code);
  END IF;
END $$;


-- ===== standard_validation_logs =====
CREATE TABLE IF NOT EXISTS standard_validation_logs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE standard_validation_logs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE standard_validation_logs ADD COLUMN IF NOT EXISTS standard_type VARCHAR(50);
ALTER TABLE standard_validation_logs ADD COLUMN IF NOT EXISTS resource_type VARCHAR(100);
ALTER TABLE standard_validation_logs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'VALID';
ALTER TABLE standard_validation_logs ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE standard_validation_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== storage_config =====
CREATE TABLE IF NOT EXISTS storage_config (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE storage_config ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE storage_config ADD COLUMN IF NOT EXISTS provider VARCHAR(30) DEFAULT 'local';
ALTER TABLE storage_config ADD COLUMN IF NOT EXISTS bucket_name VARCHAR(255);
ALTER TABLE storage_config ADD COLUMN IF NOT EXISTS base_path VARCHAR(500);
ALTER TABLE storage_config ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE storage_config ADD COLUMN IF NOT EXISTS config_json TEXT;
ALTER TABLE storage_config ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== tax_records =====
CREATE TABLE IF NOT EXISTS tax_records (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE tax_records ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE tax_records ADD COLUMN IF NOT EXISTS invoice_id VARCHAR(36);
ALTER TABLE tax_records ADD COLUMN IF NOT EXISTS tax_code VARCHAR(50) DEFAULT 'VAT';
ALTER TABLE tax_records ADD COLUMN IF NOT EXISTS tax_rate FLOAT DEFAULT 0.1;
ALTER TABLE tax_records ADD COLUMN IF NOT EXISTS tax_amount FLOAT DEFAULT 0;
ALTER TABLE tax_records ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'APPLIED';
ALTER TABLE tax_records ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.invoices') IS NULL THEN
    RAISE NOTICE 'invoices missing — skip FK fk_tax_records_invoice_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_tax_records_invoice_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE tax_records
    ADD CONSTRAINT fk_tax_records_invoice_id
    FOREIGN KEY (invoice_id) REFERENCES invoices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_tax_records_invoice_id: %', SQLERRM;
END $$;

-- ===== temperature_readings =====
CREATE TABLE IF NOT EXISTS temperature_readings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE temperature_readings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE temperature_readings ADD COLUMN IF NOT EXISTS device_id VARCHAR(36);
ALTER TABLE temperature_readings ADD COLUMN IF NOT EXISTS cold_box_id VARCHAR(36);
ALTER TABLE temperature_readings ADD COLUMN IF NOT EXISTS celsius FLOAT;
ALTER TABLE temperature_readings ADD COLUMN IF NOT EXISTS recorded_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.iot_devices') IS NULL THEN
    RAISE NOTICE 'iot_devices missing — skip FK fk_temperature_readings_device_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_temperature_readings_device_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE temperature_readings
    ADD CONSTRAINT fk_temperature_readings_device_id
    FOREIGN KEY (device_id) REFERENCES iot_devices (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_temperature_readings_device_id: %', SQLERRM;
END $$;

-- ===== tenant_organization_settings =====
CREATE TABLE IF NOT EXISTS tenant_organization_settings (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE tenant_organization_settings ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE tenant_organization_settings ADD COLUMN IF NOT EXISTS tenant_id VARCHAR(36);
ALTER TABLE tenant_organization_settings ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE tenant_organization_settings ADD COLUMN IF NOT EXISTS setting_key VARCHAR(100);
ALTER TABLE tenant_organization_settings ADD COLUMN IF NOT EXISTS setting_value TEXT;
ALTER TABLE tenant_organization_settings ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'GENERAL';
ALTER TABLE tenant_organization_settings ADD COLUMN IF NOT EXISTS is_secret BOOLEAN DEFAULT FALSE;
ALTER TABLE tenant_organization_settings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.enterprise_tenants') IS NULL THEN
    RAISE NOTICE 'enterprise_tenants missing — skip FK fk_tenant_organization_settings_tenant_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_tenant_organization_settings_tenant_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE tenant_organization_settings
    ADD CONSTRAINT fk_tenant_organization_settings_tenant_id
    FOREIGN KEY (tenant_id) REFERENCES enterprise_tenants (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_tenant_organization_settings_tenant_id: %', SQLERRM;
END $$;
DO $$
BEGIN
  IF to_regclass('public.enterprise_organizations') IS NULL THEN
    RAISE NOTICE 'enterprise_organizations missing — skip FK fk_tenant_organization_settings_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_tenant_organization_settings_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE tenant_organization_settings
    ADD CONSTRAINT fk_tenant_organization_settings_organization_id
    FOREIGN KEY (organization_id) REFERENCES enterprise_organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_tenant_organization_settings_organization_id: %', SQLERRM;
END $$;

-- ===== test_catalogs =====
CREATE TABLE IF NOT EXISTS test_catalogs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE test_catalogs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE test_catalogs ADD COLUMN IF NOT EXISTS code VARCHAR(50);
ALTER TABLE test_catalogs ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE test_catalogs ADD COLUMN IF NOT EXISTS category VARCHAR(100);
ALTER TABLE test_catalogs ADD COLUMN IF NOT EXISTS sample_type VARCHAR(100);
ALTER TABLE test_catalogs ADD COLUMN IF NOT EXISTS price FLOAT DEFAULT 0;
ALTER TABLE test_catalogs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_test_catalogs_code ON test_catalogs (code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_test_catalogs_code'
  ) THEN
    ALTER TABLE test_catalogs
      ADD CONSTRAINT uq_test_catalogs_code UNIQUE (code);
  END IF;
END $$;


-- ===== test_results =====
CREATE TABLE IF NOT EXISTS test_results (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE test_results ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS order_item_id VARCHAR(36);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS test_name VARCHAR(255);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS result_value VARCHAR(255);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS unit VARCHAR(50);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS reference_range VARCHAR(255);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS flag VARCHAR(20) DEFAULT 'NORMAL';
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS interpretation TEXT;
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS approval_status VARCHAR(30) DEFAULT 'PENDING';
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS approved_by VARCHAR(255);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS approved_at VARCHAR(100);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS doctor_license VARCHAR(100);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS signature_id VARCHAR(100);
ALTER TABLE test_results ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;




-- ===== transport_boxes =====
CREATE TABLE IF NOT EXISTS transport_boxes (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE transport_boxes ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE transport_boxes ADD COLUMN IF NOT EXISTS box_code VARCHAR(50);
ALTER TABLE transport_boxes ADD COLUMN IF NOT EXISTS driver_id VARCHAR(36);
ALTER TABLE transport_boxes ADD COLUMN IF NOT EXISTS temperature FLOAT DEFAULT 4.0;
ALTER TABLE transport_boxes ADD COLUMN IF NOT EXISTS battery_level INTEGER DEFAULT 100;
ALTER TABLE transport_boxes ADD COLUMN IF NOT EXISTS latitude VARCHAR(50);
ALTER TABLE transport_boxes ADD COLUMN IF NOT EXISTS longitude VARCHAR(50);
ALTER TABLE transport_boxes ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'ONLINE';
ALTER TABLE transport_boxes ADD COLUMN IF NOT EXISTS alert_status VARCHAR(50) DEFAULT 'NORMAL';
ALTER TABLE transport_boxes ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE transport_boxes ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_transport_boxes_box_code ON transport_boxes (box_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_transport_boxes_box_code'
  ) THEN
    ALTER TABLE transport_boxes
      ADD CONSTRAINT uq_transport_boxes_box_code UNIQUE (box_code);
  END IF;
END $$;


-- ===== users =====
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE users ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(30);
ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(50) DEFAULT 'PATIENT';
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id VARCHAR(36);
ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);
CREATE INDEX IF NOT EXISTS ix_users_organization_id ON users (organization_id);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_users_email'
  ) THEN
    ALTER TABLE users
      ADD CONSTRAINT uq_users_email UNIQUE (email);
  END IF;
END $$;

DO $$
BEGIN
  IF to_regclass('public.organizations') IS NULL THEN
    RAISE NOTICE 'organizations missing — skip FK fk_users_organization_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_users_organization_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE users
    ADD CONSTRAINT fk_users_organization_id
    FOREIGN KEY (organization_id) REFERENCES organizations (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_users_organization_id: %', SQLERRM;
END $$;

-- ===== webhook_delivery_logs =====
CREATE TABLE IF NOT EXISTS webhook_delivery_logs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE webhook_delivery_logs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE webhook_delivery_logs ADD COLUMN IF NOT EXISTS webhook_id VARCHAR(36);
ALTER TABLE webhook_delivery_logs ADD COLUMN IF NOT EXISTS event_type VARCHAR(50);
ALTER TABLE webhook_delivery_logs ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE webhook_delivery_logs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'PENDING';
ALTER TABLE webhook_delivery_logs ADD COLUMN IF NOT EXISTS response_code INTEGER;
ALTER TABLE webhook_delivery_logs ADD COLUMN IF NOT EXISTS error_message TEXT;
ALTER TABLE webhook_delivery_logs ADD COLUMN IF NOT EXISTS delivered_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE webhook_delivery_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;



DO $$
BEGIN
  IF to_regclass('public.webhook_endpoints') IS NULL THEN
    RAISE NOTICE 'webhook_endpoints missing — skip FK fk_webhook_delivery_logs_webhook_id';
    RETURN;
  END IF;
  IF EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'fk_webhook_delivery_logs_webhook_id'
  ) THEN
    RETURN;
  END IF;
  ALTER TABLE webhook_delivery_logs
    ADD CONSTRAINT fk_webhook_delivery_logs_webhook_id
    FOREIGN KEY (webhook_id) REFERENCES webhook_endpoints (id);
EXCEPTION WHEN others THEN
  RAISE NOTICE 'skip FK fk_webhook_delivery_logs_webhook_id: %', SQLERRM;
END $$;

-- ===== webhook_endpoints =====
CREATE TABLE IF NOT EXISTS webhook_endpoints (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE webhook_endpoints ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE webhook_endpoints ADD COLUMN IF NOT EXISTS webhook_code VARCHAR(50);
ALTER TABLE webhook_endpoints ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE webhook_endpoints ADD COLUMN IF NOT EXISTS target_url VARCHAR(500);
ALTER TABLE webhook_endpoints ADD COLUMN IF NOT EXISTS secret VARCHAR(255);
ALTER TABLE webhook_endpoints ADD COLUMN IF NOT EXISTS event_types_json TEXT DEFAULT '[]';
ALTER TABLE webhook_endpoints ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE webhook_endpoints ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_webhook_endpoints_webhook_code ON webhook_endpoints (webhook_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_webhook_endpoints_webhook_code'
  ) THEN
    ALTER TABLE webhook_endpoints
      ADD CONSTRAINT uq_webhook_endpoints_webhook_code UNIQUE (webhook_code);
  END IF;
END $$;


-- ===== webhook_idempotency_keys =====
CREATE TABLE IF NOT EXISTS webhook_idempotency_keys (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE webhook_idempotency_keys ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE webhook_idempotency_keys ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(128);
ALTER TABLE webhook_idempotency_keys ADD COLUMN IF NOT EXISTS webhook_id VARCHAR(36);
ALTER TABLE webhook_idempotency_keys ADD COLUMN IF NOT EXISTS delivery_id VARCHAR(36);
ALTER TABLE webhook_idempotency_keys ADD COLUMN IF NOT EXISTS response_json TEXT DEFAULT '{}';
ALTER TABLE webhook_idempotency_keys ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_webhook_idempotency_keys_idempotency_key ON webhook_idempotency_keys (idempotency_key);
CREATE INDEX IF NOT EXISTS ix_webhook_idempotency_keys_webhook_id ON webhook_idempotency_keys (webhook_id);



-- ===== webhook_replay_logs =====
CREATE TABLE IF NOT EXISTS webhook_replay_logs (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE webhook_replay_logs ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE webhook_replay_logs ADD COLUMN IF NOT EXISTS delivery_id VARCHAR(36);
ALTER TABLE webhook_replay_logs ADD COLUMN IF NOT EXISTS replay_token VARCHAR(64);
ALTER TABLE webhook_replay_logs ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'COMPLETED';
ALTER TABLE webhook_replay_logs ADD COLUMN IF NOT EXISTS detail_json TEXT DEFAULT '{}';
ALTER TABLE webhook_replay_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE INDEX IF NOT EXISTS ix_webhook_replay_logs_delivery_id ON webhook_replay_logs (delivery_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_webhook_replay_logs_replay_token ON webhook_replay_logs (replay_token);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_webhook_replay_logs_replay_token'
  ) THEN
    ALTER TABLE webhook_replay_logs
      ADD CONSTRAINT uq_webhook_replay_logs_replay_token UNIQUE (replay_token);
  END IF;
END $$;


-- ===== workflow_automation_events =====
CREATE TABLE IF NOT EXISTS workflow_automation_events (
    id VARCHAR(36) NOT NULL,
    PRIMARY KEY (id)
);

ALTER TABLE workflow_automation_events ADD COLUMN IF NOT EXISTS id VARCHAR(36);
ALTER TABLE workflow_automation_events ADD COLUMN IF NOT EXISTS event_code VARCHAR(50);
ALTER TABLE workflow_automation_events ADD COLUMN IF NOT EXISTS event_type VARCHAR(50);
ALTER TABLE workflow_automation_events ADD COLUMN IF NOT EXISTS source_type VARCHAR(50);
ALTER TABLE workflow_automation_events ADD COLUMN IF NOT EXISTS source_id VARCHAR(36);
ALTER TABLE workflow_automation_events ADD COLUMN IF NOT EXISTS payload_json TEXT DEFAULT '{}';
ALTER TABLE workflow_automation_events ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'RECEIVED';
ALTER TABLE workflow_automation_events ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE workflow_automation_events ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS ix_workflow_automation_events_event_code ON workflow_automation_events (event_code);

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'uq_workflow_automation_events_event_code'
  ) THEN
    ALTER TABLE workflow_automation_events
      ADD CONSTRAINT uq_workflow_automation_events_event_code UNIQUE (event_code);
  END IF;
END $$;


