# AI Components — Phase 8

## Core Packages

| Package | Path | Responsibility |
|---------|------|----------------|
| AI Platform | `app/ai_platform/` | Providers, router, prompts, safety, audit, PHI |
| Intelligent Healthcare | `app/services/intelligent_healthcare_service.py` | Phase 8 unified hub |
| AI Clinical | `app/services/ai_clinical_service.py` | Clinical interpretation + summaries |
| AI CDS | `app/services/ai_cds_service.py` | Rule engine, delta check, critical values |
| Knowledge Engine | `app/services/knowledge_engine_service.py` | Guidelines, biomarkers, diseases |
| Interpretation Engine | `app/services/interpretation_engine_service.py` | Reference ranges, critical rules |
| Standards | `app/services/healthcare_standards_service.py` | LOINC, ICD, SNOMED mappings |
| AI Operations | `app/services/ai_operations_service.py` | Cost, usage, model health |
| AI Copilot | `app/services/ai_copilot_service.py` | Role copilots |
| Voice Platform | `app/services/voice_platform_service.py` | Voice sessions (scaffold) |

## AI Gateway Components

| Component | Module | API section |
|-----------|--------|-------------|
| LLM Provider Registry | `ai_platform/registry.py` | `/llm-providers` |
| Prompt Registry | `ai_platform/prompt_registry.py` | `/prompt-registry` |
| Prompt Versioning | `ai_platform/models.py` | `/prompt-versioning` |
| Model Router | `ai_platform/router.py` | `/ai-gateway` |
| AI Safety Layer | `ai_platform/safety.py` | `/ai-safety` |
| PHI Redaction | `ai_platform/phi_redaction.py` | `/phi-redaction` |
| Prompt Audit | `ai_platform/audit.py` | `/prompt-audit` |
| Cost Analytics | `ai_operations_service.py` | `/cost-analytics` |
| Hallucination Detection | `intelligent_healthcare_service.py` | `/hallucination-detection` |
| Model Comparison | `intelligent_healthcare_service.py` | `/model-comparison` |
| Medical Guardrails | `intelligent_healthcare_service.py` | `/medical-guardrails` |
| AI Monitoring | `ai_operations_service.py` | `/ai-monitoring` |

## Clinical Components

| Component | Module | API section |
|-----------|--------|-------------|
| Clinical Rules Engine | `ai_cds_service.py` | `/clinical-rules` |
| Reference Range Engine | `interpretation_engine_service.py` | `/reference-ranges` |
| Clinical Summary | `ai_clinical_service.py` | `/clinical-summary` |
| Patient Explanation | `ai_clinical_service.py` | `/patient-explanation` |
| Clinical Recommendations | `ai_cds_service.py` | `/clinical-recommendations` |
| Predictive Analytics | population + analytics facades | `/predictive-analytics` |

## Terminology Components

| Component | Module | API section |
|-----------|--------|-------------|
| LOINC Registry | `standards_advanced_service.py` | `/loinc-registry` |
| ICD-10 Registry | `standards_advanced_service.py` | `/icd10-registry` |
| SNOMED Mapping | `standards/mapping.py` | `/snomed-mapping` |

## Scaffold Components (Phase 8)

| Component | Status | Notes |
|-----------|--------|-------|
| Drug Knowledge Layer | SCAFFOLD | Sample formulary entries; extend with RxNorm |
| Medical OCR Platform | SCAFFOLD | Pipeline definitions; no vision provider yet |
| Voice Clinical Platform | SCAFFOLD | In-memory sessions via voice_platform |

## Reports

| Report | Path |
|--------|------|
| AI Readiness | `backend/generated_release/AI_READINESS_REPORT.json` |
| AI Governance | `backend/generated_release/AI_GOVERNANCE_REPORT.json` |
| Hub Verify | `backend/generated_release/INTELLIGENT_HEALTHCARE_REPORT.json` |
