# Regional Architecture — Phase 9

## Mission

Prepare DxCon for deployment across multiple countries and regions with data residency awareness, regional compliance, and cloud provider abstraction.

## Hub

- **Web:** `/regional-cloud`
- **API:** `/api/v1/regional-cloud/*`
- **Service:** `app.services.regional_cloud_service`

## Supported Regions (Phase 9)

| Code | Region | Timezone | Currency | Locale |
|------|--------|----------|----------|--------|
| VN | Vietnam | Asia/Ho_Chi_Minh | VND | vi-VN |
| US | United States | America/New_York | USD | en-US |
| EU | European Union | Europe/Berlin | EUR | en-GB |
| SG | Singapore | Asia/Singapore | SGD | en-SG |

## Module Layers

```
┌─────────────────────────────────────────────────────────┐
│  Regional Analytics · Monitoring · Partner Portal       │
├─────────────────────────────────────────────────────────┤
│  Marketplace · Federation · Geo Replication             │
├─────────────────────────────────────────────────────────┤
│  Compliance (HIPAA, GDPR, PDPA, ISO27001, SOC2)         │
├─────────────────────────────────────────────────────────┤
│  Localization (i18n, Language, Currency, Tax, TZ)       │
├─────────────────────────────────────────────────────────┤
│  Cloud Abstraction (AWS, Azure, GCP, Render, On-prem)   │
├─────────────────────────────────────────────────────────┤
│  Backup · Disaster Recovery · Regional Deployment       │
└─────────────────────────────────────────────────────────┘
```

## Governance

- Backward compatible with all Phase 1–8 hubs
- No destructive database migrations
- PostgreSQL-only persistence
- Multi-region ready architecture (scaffold where noted)

## Legacy Integration

| Module | Legacy hub |
|--------|--------------|
| Regional Deployment | `/production-deployment` |
| Cross-region Federation | `/federation-platform` |
| Regional Marketplace | `/marketplace-platform` |
| Backup / DR | `/backup-recovery` |
| Compliance | `/security-compliance` |
| Localization | `/white-label` |

## Verification

```bash
python scripts/verify_regional_cloud.py
```
