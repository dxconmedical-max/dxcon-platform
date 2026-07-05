# Compliance Guide — Phase 9

## Purpose

DxCon Phase 9 maps regional compliance requirements to platform controls without breaking backward compatibility.

## Frameworks

### HIPAA (US Healthcare)

| Control | Implementation |
|---------|------------------|
| PHI access audit | `security_compliance_service` PHI audit |
| Encryption | TLS in transit; PostgreSQL at rest (provider-managed) |
| BAA required | Documented in deployment checklist |

**Status:** PREPARED

### GDPR (EU Personal Data)

| Control | Implementation |
|---------|------------------|
| Consent | Patient consent models |
| Erasure | Admin data lifecycle tools |
| DPIA | Enterprise compliance export |

**Status:** PREPARED

### PDPA (Singapore / ASEAN)

| Control | Implementation |
|---------|------------------|
| Consent | Tenant organization settings |
| Cross-border transfer | Federation consent records |

**Status:** PREPARED

### ISO 27001 (ISMS)

| Control | Implementation |
|---------|------------------|
| Risk assessment | Security compliance dashboard |
| Asset inventory | Route inventory + API registry |
| Incident response | Operations runbooks + AI incident summary |

**Status:** PREPARATION

### SOC 2 (Trust Services)

| Control | Implementation |
|---------|------------------|
| Security | RBAC, audit logs, rate limits |
| Availability | Health probes, monitoring center |
| Confidentiality | PHI redaction, secret masking |

**Status:** PREPARATION

## Regional Compliance Hub

Access compliance status at:

- Web: `/regional-cloud/regional-compliance`
- API: `GET /api/v1/regional-cloud/regional-compliance`

Individual framework sections:

- `/regional-cloud/hipaa`
- `/regional-cloud/gdpr`
- `/regional-cloud/pdpa`
- `/regional-cloud/iso27001`
- `/regional-cloud/soc2`

## Governance Rules

1. No destructive database migrations
2. Backward compatible API surface
3. PostgreSQL-only ORM access
4. Audit trail for PHI and security events
5. Data residency awareness per region config

## Verification

```bash
cd backend
python scripts/verify_regional_cloud.py
```

Generates `REGIONAL_READINESS_REPORT.json` and `DEPLOYMENT_REPORT.json`.
