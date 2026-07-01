import json
import uuid

from app.core.statuses import (
    EVIDENCE_LEVEL_A,
    EVIDENCE_LEVEL_B,
    GUIDELINE_PACK_CAP,
    GUIDELINE_PACK_CDC,
    GUIDELINE_PACK_CLSI,
    GUIDELINE_PACK_IFCC,
    GUIDELINE_PACK_VN_MOH,
    GUIDELINE_PACK_WHO,
)
from app.extensions.db import db
from app.models.knowledge_engine import (
    Biomarker,
    ClinicalGuideline,
    DiseaseProfile,
    MedicalKnowledge,
    ReferenceLibrary,
)

DEFAULT_GUIDELINE_PACKS = (
    GUIDELINE_PACK_WHO,
    GUIDELINE_PACK_CLSI,
    GUIDELINE_PACK_IFCC,
    GUIDELINE_PACK_CAP,
    GUIDELINE_PACK_CDC,
    GUIDELINE_PACK_VN_MOH,
)

RULE_CHAINS = [
    {
        "chain_code": "CHAIN-DM-PANEL",
        "name": "Diabetes marker chain",
        "markers": ["GLU", "HBA1C"],
        "disease_code": "DM-T2",
        "steps": [
            {"marker": "GLU", "operator": ">=", "value": 126},
            {"marker": "HBA1C", "operator": ">=", "value": 6.5},
        ],
    },
    {
        "chain_code": "CHAIN-CKD-PANEL",
        "name": "CKD marker chain",
        "markers": ["CREA", "EGFR"],
        "disease_code": "CKD",
        "steps": [
            {"marker": "CREA", "operator": ">=", "value": 1.5},
            {"marker": "EGFR", "operator": "<", "value": 60},
        ],
    },
]


class KnowledgeError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _parse_float(value):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _json_list(raw):
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except (TypeError, json.JSONDecodeError):
        return []


def _json_dict(raw):
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}


def _eval_step(value, operator, threshold):
    if value is None:
        return False
    if operator == ">=":
        return value >= threshold
    if operator == ">":
        return value > threshold
    if operator == "<=":
        return value <= threshold
    if operator == "<":
        return value < threshold
    if operator == "==":
        return value == threshold
    return False


class KnowledgeEngineService:

    @staticmethod
    def ensure_default_content():
        if MedicalKnowledge.query.first():
            return {"seeded": False}

        packs = DEFAULT_GUIDELINE_PACKS
        for pack in packs:
            db.session.add(
                ClinicalGuideline(
                    guideline_code=f"GL-{pack}-001",
                    pack_source=pack,
                    title=f"{pack} laboratory practice overview",
                    version="1.0",
                    content=f"Versioned guideline content from {pack}.",
                    evidence_level=EVIDENCE_LEVEL_A if pack in (GUIDELINE_PACK_WHO, GUIDELINE_PACK_CLSI) else EVIDENCE_LEVEL_B,
                    citation_json=json.dumps({"source": pack, "year": 2024}),
                    test_codes_json=json.dumps(["GLU", "HGB", "CREA"]),
                )
            )

        db.session.add(
            DiseaseProfile(
                disease_code="DM-T2",
                name="Type 2 Diabetes Mellitus",
                icd10="E11",
                description="Chronic hyperglycemia pattern",
                test_codes_json=json.dumps(["GLU", "HBA1C"]),
                pattern_json=json.dumps({"GLU": {"min": 126}, "HBA1C": {"min": 6.5}}),
                evidence_level=EVIDENCE_LEVEL_A,
            )
        )
        db.session.add(
            DiseaseProfile(
                disease_code="CKD",
                name="Chronic Kidney Disease",
                icd10="N18",
                description="Reduced kidney function pattern",
                test_codes_json=json.dumps(["CREA", "EGFR", "BUN"]),
                pattern_json=json.dumps({"CREA": {"min": 1.5}, "EGFR": {"max": 60}}),
                evidence_level=EVIDENCE_LEVEL_B,
            )
        )

        biomarkers = [
            ("BM-GLU", "Glucose", "GLU", "mg/dL", ["HBA1C"], ["DM-T2"]),
            ("BM-HBA1C", "HbA1c", "HBA1C", "%", ["GLU"], ["DM-T2"]),
            ("BM-CREA", "Creatinine", "CREA", "mg/dL", ["EGFR", "BUN"], ["CKD"]),
            ("BM-EGFR", "eGFR", "EGFR", "mL/min", ["CREA"], ["CKD"]),
        ]
        for code, name, test_code, unit, related_bm, related_dis in biomarkers:
            db.session.add(
                Biomarker(
                    biomarker_code=code,
                    name=name,
                    test_code=test_code,
                    unit=unit,
                    related_biomarkers_json=json.dumps(related_bm),
                    related_diseases_json=json.dumps(related_dis),
                    evidence_level=EVIDENCE_LEVEL_B,
                )
            )

        references = [
            ("REF-GLU-WHO", "GLU", "Glucose", 70, 100, "mg/dL", GUIDELINE_PACK_WHO),
            ("REF-HGB-CLSI", "HGB", "Hemoglobin", 13.5, 17.5, "g/dL", GUIDELINE_PACK_CLSI),
            ("REF-CREA-IFCC", "CREA", "Creatinine", 0.7, 1.3, "mg/dL", GUIDELINE_PACK_IFCC),
            ("REF-GLU-VNMOH", "GLU", "Glucose", 74, 106, "mg/dL", GUIDELINE_PACK_VN_MOH),
        ]
        for ref_code, test_code, test_name, low, high, unit, pack in references:
            db.session.add(
                ReferenceLibrary(
                    reference_code=ref_code,
                    test_code=test_code,
                    test_name=test_name,
                    low_value=low,
                    high_value=high,
                    unit=unit,
                    source_pack=pack,
                    version="1.0",
                    citation_json=json.dumps({"source": pack, "document": "reference intervals"}),
                )
            )

        knowledge_rows = [
            ("KN-DM-001", "Diabetes screening", "Endocrine", "Fasting glucose and HbA1c support diabetes screening.", ["diabetes", "glucose"], GUIDELINE_PACK_CDC),
            ("KN-CKD-001", "CKD staging", "Nephrology", "Creatinine and eGFR are core markers for CKD assessment.", ["ckd", "kidney"], GUIDELINE_PACK_CAP),
            ("KN-LIPID-001", "Cardiovascular risk", "Cardiology", "Lipid panel informs ASCVD risk stratification.", ["lipid", "cardiovascular"], GUIDELINE_PACK_WHO),
        ]
        for code, title, category, content, tags, pack in knowledge_rows:
            db.session.add(
                MedicalKnowledge(
                    knowledge_code=code,
                    title=title,
                    category=category,
                    content=content,
                    tags_json=json.dumps(tags),
                    evidence_level=EVIDENCE_LEVEL_B,
                    source_pack=pack,
                    version="1.0",
                    citation_json=json.dumps({"source": pack}),
                )
            )

        db.session.commit()
        return {"seeded": True, "packs": len(packs)}


class KnowledgeSearchService:

    @staticmethod
    def search(query=None, category=None, source_pack=None, page=1, page_size=50):
        KnowledgeEngineService.ensure_default_content()
        q = MedicalKnowledge.query.filter_by(is_active=True)
        if category:
            q = q.filter(MedicalKnowledge.category.ilike(f"%{category}%"))
        if source_pack:
            q = q.filter(MedicalKnowledge.source_pack == source_pack.upper())
        if query:
            like = f"%{query}%"
            q = q.filter(
                db.or_(
                    MedicalKnowledge.title.ilike(like),
                    MedicalKnowledge.content.ilike(like),
                    MedicalKnowledge.knowledge_code.ilike(like),
                )
            )
        total = q.count()
        rows = (
            q.order_by(MedicalKnowledge.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"total": total, "page": page, "page_size": page_size, "items": [row.to_dict() for row in rows]}

    @staticmethod
    def create(data):
        code = data.get("knowledge_code") or f"KN-{uuid.uuid4().hex[:8].upper()}"
        row = MedicalKnowledge(
            knowledge_code=code,
            title=data.get("title") or "Untitled",
            category=data.get("category"),
            content=data.get("content") or "",
            tags_json=json.dumps(data.get("tags") or []),
            evidence_level=data.get("evidence_level") or EVIDENCE_LEVEL_B,
            source_pack=data.get("source_pack"),
            version=data.get("version") or "1.0",
            citation_json=json.dumps(data.get("citation") or {}),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def get(knowledge_id):
        row = MedicalKnowledge.query.get(knowledge_id)
        if not row:
            raise KnowledgeError("Knowledge entry not found", 404)
        return row.to_dict()


class GuidelinePackService:

    @staticmethod
    def list_packs():
        KnowledgeEngineService.ensure_default_content()
        return {
            "packs": [
                {
                    "pack_source": pack,
                    "count": ClinicalGuideline.query.filter_by(pack_source=pack, is_active=True).count(),
                }
                for pack in DEFAULT_GUIDELINE_PACKS
            ]
        }

    @staticmethod
    def list_guidelines(pack_source=None, version=None, page=1, page_size=50):
        KnowledgeEngineService.ensure_default_content()
        q = ClinicalGuideline.query.filter_by(is_active=True)
        if pack_source:
            q = q.filter(ClinicalGuideline.pack_source == pack_source.upper())
        if version:
            q = q.filter(ClinicalGuideline.version == version)
        total = q.count()
        rows = (
            q.order_by(ClinicalGuideline.pack_source.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return {"total": total, "page": page, "page_size": page_size, "guidelines": [row.to_dict() for row in rows]}

    @staticmethod
    def create(data):
        pack = (data.get("pack_source") or "").upper()
        if pack and pack not in DEFAULT_GUIDELINE_PACKS:
            raise KnowledgeError(f"Unsupported pack source: {pack}")
        code = data.get("guideline_code") or f"GL-{uuid.uuid4().hex[:8].upper()}"
        row = ClinicalGuideline(
            guideline_code=code,
            pack_source=pack or GUIDELINE_PACK_WHO,
            title=data.get("title") or "Guideline",
            version=data.get("version") or "1.0",
            content=data.get("content") or "",
            evidence_level=data.get("evidence_level") or EVIDENCE_LEVEL_B,
            citation_json=json.dumps(data.get("citation") or {}),
            test_codes_json=json.dumps(data.get("test_codes") or []),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def get(guideline_id):
        row = ClinicalGuideline.query.get(guideline_id)
        if not row:
            raise KnowledgeError("Guideline not found", 404)
        return row.to_dict()


class BiomarkerService:

    @staticmethod
    def list_biomarkers(query=None, page=1, page_size=50):
        KnowledgeEngineService.ensure_default_content()
        q = Biomarker.query.filter_by(is_active=True)
        if query:
            like = f"%{query}%"
            q = q.filter(
                db.or_(
                    Biomarker.name.ilike(like),
                    Biomarker.biomarker_code.ilike(like),
                    Biomarker.test_code.ilike(like),
                )
            )
        total = q.count()
        rows = q.order_by(Biomarker.name.asc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"total": total, "page": page, "page_size": page_size, "biomarkers": [row.to_dict() for row in rows]}

    @staticmethod
    def get_by_code(biomarker_code):
        KnowledgeEngineService.ensure_default_content()
        row = Biomarker.query.filter_by(biomarker_code=biomarker_code.upper(), is_active=True).first()
        if not row:
            raise KnowledgeError("Biomarker not found", 404)
        return row.to_dict()

    @staticmethod
    def relationships(biomarker_code):
        row_data = BiomarkerService.get_by_code(biomarker_code)
        related_codes = _json_list(row_data.get("related_biomarkers_json"))
        disease_codes = _json_list(row_data.get("related_diseases_json"))
        related = Biomarker.query.filter(Biomarker.biomarker_code.in_(related_codes)).all() if related_codes else []
        diseases = DiseaseProfile.query.filter(DiseaseProfile.disease_code.in_(disease_codes)).all() if disease_codes else []
        return {
            "biomarker": row_data,
            "related_biomarkers": [item.to_dict() for item in related],
            "related_diseases": [item.to_dict() for item in diseases],
        }


class DiseaseMappingService:

    @staticmethod
    def list_diseases(query=None, page=1, page_size=50):
        KnowledgeEngineService.ensure_default_content()
        q = DiseaseProfile.query.filter_by(is_active=True)
        if query:
            like = f"%{query}%"
            q = q.filter(
                db.or_(
                    DiseaseProfile.name.ilike(like),
                    DiseaseProfile.disease_code.ilike(like),
                    DiseaseProfile.icd10.ilike(like),
                )
            )
        total = q.count()
        rows = q.order_by(DiseaseProfile.name.asc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"total": total, "page": page, "page_size": page_size, "diseases": [row.to_dict() for row in rows]}

    @staticmethod
    def get_by_code(disease_code):
        KnowledgeEngineService.ensure_default_content()
        row = DiseaseProfile.query.filter_by(disease_code=disease_code.upper(), is_active=True).first()
        if not row:
            raise KnowledgeError("Disease profile not found", 404)
        return row.to_dict()

    @staticmethod
    def tests_for_disease(disease_code):
        row = DiseaseMappingService.get_by_code(disease_code)
        return {"disease_code": row["disease_code"], "tests": _json_list(row.get("test_codes_json"))}

    @staticmethod
    def diseases_for_test(test_code):
        KnowledgeEngineService.ensure_default_content()
        code = test_code.upper()
        matches = []
        for row in DiseaseProfile.query.filter_by(is_active=True).all():
            tests = _json_list(row.test_codes_json)
            if code in tests:
                matches.append(row.to_dict())
        return {"test_code": code, "diseases": matches}


class CorrelationService:

    @staticmethod
    def match_markers(data):
        KnowledgeEngineService.ensure_default_content()
        items = data.get("items") or []
        values = {}
        for item in items:
            code = (item.get("test_code") or item.get("marker") or "").upper()
            val = _parse_float(item.get("result_value") or item.get("value"))
            if code and val is not None:
                values[code] = val

        matches = []
        for disease in DiseaseProfile.query.filter_by(is_active=True).all():
            pattern = _json_dict(disease.pattern_json)
            if not pattern:
                continue
            hit = 0
            details = []
            for marker, rule in pattern.items():
                marker = marker.upper()
                if marker not in values:
                    continue
                value = values[marker]
                matched = False
                if "min" in rule and value >= rule["min"]:
                    matched = True
                if "max" in rule and value <= rule["max"]:
                    matched = True
                if matched:
                    hit += 1
                    details.append({"marker": marker, "value": value, "rule": rule})
            if hit >= max(1, len(pattern) // 2):
                matches.append(
                    {
                        "disease_code": disease.disease_code,
                        "disease_name": disease.name,
                        "matched_markers": details,
                        "evidence_level": disease.evidence_level,
                        "confidence": round(hit / len(pattern), 2),
                    }
                )

        multi_marker = []
        abnormal = [code for code, value in values.items() if value is not None]
        if len(abnormal) >= 2:
            multi_marker.append(
                {
                    "type": "multi_marker_correlation",
                    "markers": abnormal,
                    "message": "Multiple abnormal markers detected",
                }
            )

        return {
            "matches": matches,
            "multi_marker_correlations": multi_marker,
            "marker_count": len(values),
        }

    @staticmethod
    def evaluate_chains(data):
        items = data.get("items") or []
        values = {}
        for item in items:
            code = (item.get("test_code") or item.get("marker") or "").upper()
            val = _parse_float(item.get("result_value") or item.get("value"))
            if code and val is not None:
                values[code] = val

        chain_code = (data.get("chain_code") or "").upper()
        chains = RULE_CHAINS
        if chain_code:
            chains = [chain for chain in RULE_CHAINS if chain["chain_code"] == chain_code]
            if not chains:
                raise KnowledgeError("Rule chain not found", 404)

        results = []
        for chain in chains:
            steps_passed = []
            for step in chain["steps"]:
                marker = step["marker"].upper()
                passed = _eval_step(values.get(marker), step["operator"], step["value"])
                steps_passed.append({"marker": marker, "passed": passed, "step": step})
            all_passed = all(step["passed"] for step in steps_passed) if steps_passed else False
            results.append(
                {
                    "chain_code": chain["chain_code"],
                    "name": chain["name"],
                    "disease_code": chain["disease_code"],
                    "steps": steps_passed,
                    "matched": all_passed,
                }
            )

        return {"chains": results, "evaluated": len(results)}


class ReferenceLibraryService:

    @staticmethod
    def list_references(test_code=None, source_pack=None):
        KnowledgeEngineService.ensure_default_content()
        q = ReferenceLibrary.query.filter_by(is_active=True)
        if test_code:
            q = q.filter(ReferenceLibrary.test_code == test_code.upper())
        if source_pack:
            q = q.filter(ReferenceLibrary.source_pack == source_pack.upper())
        return {"references": [row.to_dict() for row in q.order_by(ReferenceLibrary.test_code.asc()).all()]}
