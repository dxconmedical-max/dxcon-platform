# DxCon Module Map

## API Modules

- `backend/app/api/auth/` — authentication and session APIs
- `backend/app/api/system/` — health, storage, and system diagnostics
- `backend/app/api/files/` — object storage file service
- `backend/app/api/ai_platform/` — AI provider, prompt, inference, audit APIs
- `backend/app/api/connectors/` — integration connector registry
- `backend/app/api/integration_platform/` — plugins, events, webhooks, sandbox

## Platform Modules

- `backend/app/storage/` — local/S3 storage providers and attachment service
- `backend/app/integrations/` — connector registry, audit trail, sandbox tokens
- `backend/app/webhooks/` — webhook idempotency, replay safety, signatures
- `backend/app/events/` — domain event bus and deduplication
- `backend/app/ai_platform/` — advisory AI foundation

## Core Infrastructure

- `backend/app/core/config.py` — environment-backed settings
- `backend/app/core/config_validation.py` — startup validation and production safety checks
- `backend/app/core/logging_config.py` — JSON/text logging and redaction
- `backend/app/core/request_context.py` — request/correlation/trace propagation
- `backend/app/core/exceptions.py` — centralized exception hierarchy
- `backend/app/core/errors.py` — HTTP error handler registration

## Bootstrap

- `backend/app/bootstrap/extensions.py` — DB, JWT, storage, AI, security init
- `backend/app/bootstrap/middleware.py` — logging and request envelope middleware
- `backend/app/bootstrap/blueprints.py` — blueprint registration inventory
- `backend/app/bootstrap/errors.py` — error handler registration wrapper

## Verification Scripts

- `backend/scripts/verify_blueprint_registry.py`
- `backend/scripts/verify_env_safety.py`
- `backend/scripts/verify_enterprise_hardening_pack2.py`

## Generated Reports

- `backend/generated_release/architecture_consistency_report.json`
- `backend/generated_release/code_quality_report.json`
- `backend/generated_release/production_standard_report.json`
