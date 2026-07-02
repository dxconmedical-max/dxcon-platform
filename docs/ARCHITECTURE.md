# DxCon Platform Architecture

## Overview

DxCon is a Flask monolith with a layered backend under `backend/app/`. HTTP traffic enters through registered blueprints, passes through request-context middleware, and reaches service modules backed by SQLAlchemy models.

## Application Factory

`backend/app/__init__.py` defines `create_app()` with a stable bootstrap sequence:

1. Load and validate configuration
2. Initialize extensions (`backend/app/bootstrap/extensions.py`)
3. Register middleware (`backend/app/bootstrap/middleware.py`)
4. Register blueprints (`backend/app/bootstrap/blueprints.py`)
5. Register API error handlers (`backend/app/bootstrap/errors.py`)
6. Finalize observability and deployment startup checks

## Core Layers

| Layer | Path | Responsibility |
|------|------|----------------|
| API | `backend/app/api/` | HTTP routes and request/response wiring |
| Services | `backend/app/services/` | Business workflow orchestration |
| Models | `backend/app/models/` | SQLAlchemy persistence |
| Core | `backend/app/core/` | Config, logging, security, errors |
| Bootstrap | `backend/app/bootstrap/` | App factory registration helpers |
| Platform | `backend/app/ai_platform/`, `storage/`, `integrations/` | Cross-cutting platform services |

## Observability

- Structured JSON logging via `backend/app/core/logging_config.py`
- Request, trace, and correlation IDs via `backend/app/core/request_context.py`
- Sensitive values redacted from logs and query strings

## Error Model

Central exceptions live in `backend/app/core/exceptions.py`. API handlers in `backend/app/core/errors.py` map exceptions to consistent JSON error envelopes for `/api/*` routes.

## Deployment Shape

- WSGI entry: `backend/run.py`
- Production process wrapper: `backend/production_start.py`
- Container/build assets under repo root `deployment/`

## Design Rules

- No business logic in route handlers beyond validation and delegation
- Prefer service modules over duplicate helpers
- Keep platform modules advisory-only for AI outputs
- Avoid tracking local secrets, virtualenvs, or generated scratch artifacts in git
