# Medical AI Guide — Phase 8

## Overview

DxCon Phase 8 delivers an **Intelligent Healthcare Platform** that assists clinicians without replacing medical judgment. Every AI output is advisory and requires human review before clinical action.

## Access

| Resource | URL |
|----------|-----|
| Hub dashboard | `/intelligent-healthcare` |
| API dashboard | `GET /api/v1/intelligent-healthcare/dashboard` |
| Readiness report | `GET /api/v1/intelligent-healthcare/readiness` |

**Roles:** `SUPER_ADMIN`, `ADMIN`, `DOCTOR`

## Governance Rules

1. **No automatic diagnosis** — blocked patterns reject auto-diagnosis language
2. **Human review required** — all outputs include `human_review_required: true`
3. **PHI redaction** — identifiers stripped before external LLM calls
4. **Audit logging** — prompts and inferences recorded in `AIAuditService`
5. **Clinical disclaimer** — appended to every advisory response

## Using Role Copilots

| Copilot | Section | Purpose |
|---------|---------|---------|
| Reception | `/intelligent-healthcare/reception-copilot` | Intake assistance (advisory) |
| Doctor | `/intelligent-healthcare/doctor-copilot` | Result review support |
| Collector | `/intelligent-healthcare/collector-copilot` | Collection workflow hints |
| CEO | `/intelligent-healthcare/ceo-copilot` | Executive summaries |

Copilots do **not** execute clinical orders autonomously.

## Clinical AI Workflow

1. Lab result enters via existing result gateway
2. Reference range engine flags abnormal values
3. Clinical rules engine evaluates guideline packs
4. AI gateway generates advisory interpretation (optional)
5. Doctor reviews and approves before patient communication

## Terminology Services

- **LOINC:** validate lab test codes via `/intelligent-healthcare/loinc-registry`
- **ICD-10:** validate diagnosis codes via `/intelligent-healthcare/icd10-registry`
- **SNOMED:** crosswalk mappings via `/intelligent-healthcare/snomed-mapping`

## Monitoring & Safety

- **Cost analytics:** token usage and estimated cost
- **Hallucination detection:** citation checks, confidence thresholds, blocked patterns
- **Model comparison:** side-by-side provider routing for interpretation tasks
- **AI monitoring dashboard:** usage metrics + operations summary

## Scaffold Modules

Drug knowledge and medical OCR are scaffold-only in Phase 8. They return pipeline definitions and sample data but do not invoke external services.

## Verification

```bash
cd backend
python scripts/verify_intelligent_healthcare.py
```

Target: **100%** verify score with `AI_READINESS_REPORT.json` and `AI_GOVERNANCE_REPORT.json` generated.

## Related Documentation

- [AI Architecture](architecture/AI_ARCHITECTURE.md)
- [AI Sequence Diagrams](architecture/AI_SEQUENCE_DIAGRAMS.md)
- [AI Components](architecture/AI_COMPONENTS.md)
