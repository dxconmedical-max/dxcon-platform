# Data Warehouse Architecture (Phase 7.7)

## Purpose

Analytics export hub bridging operational DB to reporting pipelines (ETL scaffold, metrics snapshots).

## Components

- Hub: `/data-warehouse`
- API: `/api/v1/data-warehouse/*`
- Facades: existing analytics and export services

## Non-Goals (Phase 7.7)

- No destructive schema changes
- No external warehouse provisioning in this sprint

## Verification

`python scripts/verify_data_warehouse.py`
