# Partner Platform MVP

Sprint 1.1 delivers the Partner Platform needed to onboard diagnostic service partners within 30 days, extended with production-ready foundations for users, workflow, verification, API credentials, SLA, and marketplace ratings.

## Scope

### Partner types

- LABORATORY
- CLINIC
- HOSPITAL
- DOCTOR
- CORPORATE
- HOME_CARE
- IMAGING_CENTER

### Data models

| Model | Table | Purpose |
|-------|-------|---------|
| Partner | `partners` | Core partner profile, workflow status, SLA, ratings |
| PartnerBranch | `partner_branches` | Branch locations under a partner |
| PartnerService | `partner_services` | Services offered by a partner |
| PartnerDocument | `partner_documents` | Compliance and verification documents |
| PartnerCoverageArea | `partner_coverage_areas` | Geographic service coverage |
| PartnerOperatingHour | `partner_operating_hours` | Operating hours by branch/day |
| PartnerUser | `partner_users` | Partner portal users and roles |
| PartnerVerificationItem | `partner_verification_items` | Onboarding verification checklist |
| PartnerApiCredential | `partner_api_credentials` | Hashed API credentials for integrations |

### Partner workflow lifecycle

| Status | Meaning |
|--------|---------|
| DRAFT | Initial registration, not yet submitted |
| SUBMITTED | Submitted for onboarding review |
| UNDER_REVIEW | Ops team is reviewing documents |
| APPROVED | Verified and approved for activation |
| ACTIVE | Live on the marketplace |
| SUSPENDED | Temporarily disabled |
| ARCHIVED | Retired partner record |
| REJECTED | Failed verification |

**Backward compatibility:** legacy statuses `PENDING`, `APPROVED`, `REJECTED`, and `SUSPENDED` remain valid. `PENDING` partners can still be approved or rejected directly.

Typical flow:

```
DRAFT -> SUBMITTED -> UNDER_REVIEW -> APPROVED -> ACTIVE
```

### Partner user roles

| Role | Purpose |
|------|---------|
| OWNER | Primary account owner |
| ADMIN | Full partner admin access |
| MANAGER | Branch/operations manager |
| RECEPTION | Front desk operations |
| FINANCE | Billing and invoices |
| DOCTOR | Clinical reviewer |
| STAFF | General staff access |

User status: `ACTIVE`, `INVITED`, `DISABLED`

### Verification checklist

Seeded automatically on partner creation:

- BUSINESS_LICENSE
- MEDICAL_LICENSE
- TAX_CODE
- BANK_ACCOUNT
- IDENTITY_VERIFIED

Item status: `MISSING`, `SUBMITTED`, `VERIFIED`, `REJECTED`

### API credentials

- Secrets are hashed at rest (`client_secret_hash`, `api_key_hash`)
- Plaintext secrets are returned **once** on credential creation only
- List/detail endpoints never expose secrets or hashes

Credential status: `ACTIVE`, `DISABLED`, `REVOKED`

### SLA and marketplace fields

On `Partner`:

- `average_result_time_hours`
- `pickup_sla_minutes`
- `response_sla_minutes`
- `working_hours_summary`
- `rating`
- `review_count`
- `completed_orders`

On `PartnerService`:

- `average_result_time_hours` (optional service-level override)

### API integration status

| Value | Meaning |
|-------|---------|
| OFFLINE | No automated integration |
| MANUAL_UPLOAD | Manual result upload |
| REST_API | REST API integration |
| HL7 | HL7 messaging |
| FHIR | FHIR integration |

## REST API

Base path: `/api/v1/partners`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/partners` | Create partner (seeds verification checklist) |
| GET | `/api/v1/partners` | List partners (`?partner_type=&status=`) |
| GET | `/api/v1/partners/<partner_id>` | Get partner (`?detail=true` for full payload) |
| PUT | `/api/v1/partners/<partner_id>` | Update partner |
| POST | `/api/v1/partners/<partner_id>/submit` | Submit for review |
| POST | `/api/v1/partners/<partner_id>/review` | Move to under review |
| POST | `/api/v1/partners/<partner_id>/approve` | Approve partner |
| POST | `/api/v1/partners/<partner_id>/reject` | Reject partner |
| POST | `/api/v1/partners/<partner_id>/activate` | Activate approved partner |
| POST | `/api/v1/partners/<partner_id>/suspend` | Suspend partner |
| POST | `/api/v1/partners/<partner_id>/archive` | Archive partner |
| GET/POST | `/api/v1/partners/<partner_id>/users` | List/add partner users |
| GET | `/api/v1/partners/<partner_id>/verification` | List verification checklist |
| PUT | `/api/v1/partners/<partner_id>/verification/<item_id>` | Update verification item |
| GET/POST | `/api/v1/partners/<partner_id>/credentials` | List/create API credentials |
| POST | `/api/v1/partners/<partner_id>/credentials/<credential_id>/revoke` | Revoke credential |
| POST/GET | `/api/v1/partners/<partner_id>/services` | Add/list partner services |

### Create partner example

```json
POST /api/v1/partners
{
  "partner_type": "LABORATORY",
  "legal_name": "ABC Diagnostic JSC",
  "display_name": "ABC Lab",
  "tax_code": "0101234567",
  "license_number": "LAB-2024-001",
  "representative_name": "Nguyen Van A",
  "phone": "0901234567",
  "email": "contact@abclab.vn",
  "address": "123 Nguyen Trai",
  "city": "Hanoi",
  "district": "Thanh Xuan",
  "api_status": "MANUAL_UPLOAD",
  "average_result_time_hours": 24,
  "pickup_sla_minutes": 120,
  "response_sla_minutes": 30,
  "working_hours_summary": "Mon-Sat 07:00-20:00"
}
```

Partner codes are auto-generated as `PTR-<TYPE_PREFIX>-<SEQUENCE>` when not supplied (e.g. `PTR-LAB-0001`).

### Observability

| Event | Audit log | Event log |
|-------|-----------|-----------|
| Create | — | PARTNER_CREATED |
| Submit | PARTNER_SUBMITTED | PARTNER_SUBMITTED |
| Review | PARTNER_UNDER_REVIEW | PARTNER_UNDER_REVIEW |
| Approve | PARTNER_APPROVED | PARTNER_APPROVED |
| Reject | PARTNER_REJECTED | PARTNER_REJECTED |
| Activate | PARTNER_ACTIVATED | PARTNER_ACTIVATED |
| Suspend | PARTNER_SUSPENDED | PARTNER_SUSPENDED |
| Archive | PARTNER_ARCHIVED | PARTNER_ARCHIVED |
| Verification update | PARTNER_VERIFICATION_UPDATED | PARTNER_VERIFICATION_UPDATED |
| Credential create/revoke | Yes | Yes |

## Web UI

| Route | Description |
|-------|-------------|
| `/partners` | Partner list |
| `/partners/new` | Registration form |
| `/partners/<partner_id>` | Detail with workflow actions, verification checklist, SLA metrics, ratings, API credentials, services |

## Architecture

```
API / Web routes
       ↓
PartnerPlatformService  (backend/app/services/partner_platform.py)
       ↓
Models + write_audit() + write_event()
```

Routes remain thin. Business rules live in the service layer.

## Verification

```bash
cd backend
./venv/bin/python scripts/verify_partner_platform.py
./venv/bin/python -m unittest tests.test_partner_platform -v
```

## Files

**Models**

- `backend/app/models/partner.py`
- `backend/app/models/partner_branch.py`
- `backend/app/models/partner_service.py`
- `backend/app/models/partner_document.py`
- `backend/app/models/partner_coverage_area.py`
- `backend/app/models/partner_operating_hour.py`
- `backend/app/models/partner_user.py`
- `backend/app/models/partner_verification_item.py`
- `backend/app/models/partner_api_credential.py`

**Service / API / Web**

- `backend/app/services/partner_platform.py`
- `backend/app/api/partners/routes.py`
- `backend/app/web/partners.py`

**Tests / scripts / docs**

- `backend/tests/test_partner_platform.py`
- `backend/scripts/verify_partner_platform.py`
- `docs/partner/PARTNER_PLATFORM_MVP.md`

## Next steps (post-MVP)

- Partner portal login and self-service onboarding
- Email invitations for PartnerUser
- Contract and pricing linkage to existing `Contract` module
- Alembic migrations for production schema management
