# Canonical Healthcare Data Model — Release 2.0

**Schema version:** 1.0

## Entities

Defined in `app/integration/mappings/canonical.py` and extended for marketplace:

| Entity | Key fields |
|--------|------------|
| **Patient** | patient_code, full_name, date_of_birth, gender, phone, national_id, address, organization_id |
| **Order** | order_code, patient_code, ordering_doctor_code, clinic_code, laboratory_code, tests, priority, ordered_at, collection_type |
| **Sample** | sample_code, order_code, sample_type, tube_type, collected_at, received_at, condition |
| **Result** | order_code, sample_code, test_code, result_value, unit, reference_range, abnormal_flag, result_time, status |
| **Report** | report_code, order_code, version, approved_at, released_at, report_url, report_hash |
| **Integration Message** | message_id, connector_id, direction, message_type, payload_hash, status |

## Validation

Use `validate_canonical(payload, fields)` for inbound integration transforms.

## Versioning

Schema version in payload metadata: `"schema_version": "1.0"`. Breaking changes increment major version.

## Verification

`CANONICAL_MODEL_FREEZE_REPORT.json`
