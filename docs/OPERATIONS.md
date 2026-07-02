# DxCon Operations Guide

## Logging

Production and staging should run with:

```env
LOG_FORMAT=json
LOG_LEVEL=INFO
```

Logs include request ID, correlation ID, trace ID, route, status, and duration. Sensitive keys are redacted by `backend/app/core/logging_config.py`.

## Health and Diagnostics

| Endpoint / Script | Purpose |
|-------------------|---------|
| `/api/v1/system/health` | Application health |
| `/api/v1/system/storage` | Storage provider health/metrics |
| `backend/scripts/verify_blueprint_registry.py` | Route/blueprint inventory |
| `backend/scripts/verify_env_safety.py` | Env file safety |
| `backend/scripts/verify_enterprise_hardening_pack2.py` | Code quality/production standards |

## Incident Response Basics

1. Capture request ID / correlation ID from logs
2. Check observability metrics and recent deploy version (`BUILD_VERSION`, `GIT_SHA`)
3. Review `backend/generated_release/production_standard_report.json`
4. Roll back to prior tag if startup or smoke checks fail

## Backup and Restore

Use backup/restore scripts under `backend/scripts/` and deployment verification wrappers. Confirm backup restore in staging before production changes.

## Queue and Worker Placeholders

Background worker runtime may be placeholder until queue sprint work is fully promoted. Monitor `/api/v1/system/queues` and production startup logs for worker readiness messages.

## Release Isolation

Before mixed commits, run:

```bash
python backend/scripts/release_isolation.py check --release <release-id>
```

This prevents unrelated platform changes from landing in the same release commit.

## Standard Operating Checks

- No bare `except:` in application code
- No `except Exception: pass` without logging
- Config validation passes for target environment
- Full unit test suite green before promotion
