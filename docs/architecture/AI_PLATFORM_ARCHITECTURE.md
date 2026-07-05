# AI Platform Architecture (Phase 7.3)

## Purpose

Unified AI Copilot hub for reception, doctor, collector, and lab workflows with advisory-only outputs, PHI redaction, safety policies, and audit trails.

## Components

| Layer | Module | Role |
|-------|--------|------|
| Hub | `/ai-copilot` | Admin dashboard |
| API | `/api/v1/ai-copilot/*` | Readiness, copilot sections, audit |
| Prompts | `app.ai_platform.prompt_registry` | Versioned prompt templates |
| Safety | `app.ai_platform.safety` | Blocked patterns, disclaimers |
| Router | `app.ai_platform.router` | Model routing (advisory) |
| Audit | `app.ai_platform.audit` | Usage and decision logging |
| PHI | `app.ai_platform.phi_redaction` | Redact before external calls |

## Principles

- **Advisory only** — no autonomous clinical actions
- **Tenant-aware** — respects multi-tenant context from Phase 7.1
- **Backward compatible** — existing AI routes unchanged

## Readiness

Run `python scripts/verify_ai_copilot.py` for hub, API, and legacy route checks.
