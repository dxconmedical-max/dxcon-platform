# Population Health Architecture (Phase 7.8)

## Purpose

Cohort dashboards, risk stratification scaffolds, and public-health reporting hooks.

## Components

- Hub: `/population-health`
- API: `/api/v1/population-health/*`

## Principles

- Aggregated metrics only at hub level
- Tenant-scoped where applicable

## Verification

`python scripts/verify_population_health.py`
