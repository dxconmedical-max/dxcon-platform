# AI Architecture — Phase 8 Intelligent Healthcare Platform

## Mission

Transform DxCon into an AI-assisted healthcare platform where **human medical review is mandatory** for all clinical outputs.

## Principles

| Principle | Implementation |
|-----------|----------------|
| Advisory only | `AISafetyPolicy.wrap_output()` on all clinical AI responses |
| No auto-diagnosis | Blocked patterns + `doctor_review_required: true` |
| PHI protection | `phi_redaction` before external LLM calls |
| Backward compatible | Legacy hubs preserved: `/ai-clinical`, `/ai-copilot`, `/ai-operations` |
| PostgreSQL + SQLAlchemy | ORM-only data access; no destructive migrations |
| Audit trail | `AIAuditService` logs prompts, inferences, safety blocks |

## Hub

- **Web:** `/intelligent-healthcare`
- **API:** `/api/v1/intelligent-healthcare/*`
- **Service:** `app.services.intelligent_healthcare_service`

## Layer Model

```
┌─────────────────────────────────────────────────────────┐
│  Role Copilots (Reception, Doctor, Collector, CEO)      │
├─────────────────────────────────────────────────────────┤
│  Clinical AI (Summary, Explanation, Recommendations)      │
├─────────────────────────────────────────────────────────┤
│  Knowledge + Rules (Guidelines, Ranges, CDS, Drugs)       │
├─────────────────────────────────────────────────────────┤
│  Terminology (LOINC, ICD-10, SNOMED)                      │
├─────────────────────────────────────────────────────────┤
│  AI Gateway (Providers, Router, Prompts, Safety, Audit) │
├─────────────────────────────────────────────────────────┤
│  Monitoring (Cost, Usage, Hallucination Detection)        │
└─────────────────────────────────────────────────────────┘
```

## Module Status

| Module | Status | Legacy route |
|--------|--------|--------------|
| AI Clinical Platform | READY | `/ai-clinical` |
| Medical Knowledge Base | READY | `/api/v1/guidelines` |
| Clinical Rules Engine | READY | `/api/v1/ai-cds` |
| Reference Range Engine | READY | `/api/v1/reference-ranges` |
| LOINC / ICD-10 / SNOMED | READY | `/standards-advanced` |
| Drug Knowledge | SCAFFOLD | — |
| Medical OCR | SCAFFOLD | — |
| Voice Clinical | SCAFFOLD | `/voice-platform` |
| Copilots | READY | `/ai-copilot` |
| AI Gateway / Monitoring | READY | `/ai-operations` |

## Verification

```bash
python scripts/verify_intelligent_healthcare.py
```

Generates `AI_READINESS_REPORT.json` and `AI_GOVERNANCE_REPORT.json`.
