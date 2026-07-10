# Data Ownership Map — Release 2.0

## Domain ownership

| Domain | Primary tables | Owner module |
|--------|----------------|--------------|
| Identity | `users`, `organization_memberships` | `app/models/user.py`, auth services |
| Organization | `organizations`, `partners` | partner foundation |
| Clinical orders | `orders`, `order_items` | order services |
| Samples | `samples`, `sample_collections` | lab/collector services |
| Results | `test_results`, `lab_results` | result gateway |
| Reports | `reports`, `report_versions` | reporting engine |
| Billing | `invoices`, `billing_accounts` | billing |
| Payments | `payments`, `payment_transactions` | payment gateway |
| Integration | `intg_*` | `app/integration/` |
| Marketplace | `marketplace_bookings`, `mp_*` | marketplace / patient_marketplace |
| MDM | `mdm_*`, diagnostic catalog | mdm |
| Audit | `audit_logs`, `intg_audit_events` | core audit |

## Tenant column

Business tables owned by a partner organization must include `organization_id`. Platform-global reference data (diagnostic catalog templates, system settings) may omit it with explicit documentation.

## Cross-domain references

- Orders reference patients and organizations
- Results reference orders and samples
- Integration messages reference connectors and organizations
- Marketplace bookings reference providers (organizations) and patients

## Verification

`DATABASE_FREEZE_REPORT.json` lists tables missing tenant columns for review. Shared reference tables are exempt.
