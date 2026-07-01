import json
import uuid

from app.core.statuses import (
    CDS_PANEL_CBC,
    CDS_PANEL_CHEMISTRY,
    CDS_PANEL_COAGULATION,
    CDS_PANEL_HBA1C,
    CDS_PANEL_KIDNEY,
    CDS_PANEL_LIPID,
    CDS_PANEL_LIVER,
    CDS_PANEL_THYROID,
    CDS_PANEL_URINALYSIS,
    CRITICAL_ALERT_CORRELATION,
    CRITICAL_ALERT_DELTA,
    CRITICAL_ALERT_PANIC,
    CRITICAL_ALERT_REPEATED,
)
from app.extensions.db import db
from app.models.ai_cds import (
    ClinicalDeltaCheck,
    ClinicalGuidelinePack,
    ClinicalRecommendation,
    ClinicalRiskAssessment,
    ClinicalRuleDefinition,
    CriticalAlertEvent,
)
from app.models.lab_result import LabResult
from app.models.lab_result_item import LabResultItem
from app.services.interpretation_engine_service import (
    CriticalValueService,
    InterpretationEngine,
    ReferenceRangeService,
)


PANEL_TEST_MAP = {
    CDS_PANEL_CBC: ["WBC", "RBC", "HGB", "HCT", "PLT"],
    CDS_PANEL_CHEMISTRY: ["GLU", "BUN", "CREA", "NA", "K", "CL"],
    CDS_PANEL_LIVER: ["ALT", "AST", "ALP", "TBIL", "ALB"],
    CDS_PANEL_KIDNEY: ["CREA", "BUN", "EGFR", "UREA"],
    CDS_PANEL_LIPID: ["CHOL", "TG", "HDL", "LDL"],
    CDS_PANEL_HBA1C: ["HBA1C"],
    CDS_PANEL_THYROID: ["TSH", "FT4", "FT3"],
    CDS_PANEL_URINALYSIS: ["U-PRO", "U-GLU", "U-LEU", "U-NIT"],
    CDS_PANEL_COAGULATION: ["PT", "INR", "APTT"],
}


class CDSError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _parse_float(value):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _detect_panel(test_code, test_name):
    code = (test_code or "").upper()
    name = (test_name or "").lower()
    for panel, codes in PANEL_TEST_MAP.items():
        if code in codes:
            return panel
        if panel == CDS_PANEL_HBA1C and "hba1c" in name:
            return panel
        if panel == CDS_PANEL_LIVER and any(k in name for k in ("alt", "ast", "bilirubin", "albumin")):
            return panel
        if panel == CDS_PANEL_KIDNEY and any(k in name for k in ("creatinine", "urea", "egfr")):
            return panel
        if panel == CDS_PANEL_LIPID and any(k in name for k in ("cholesterol", "triglyceride", "hdl", "ldl")):
            return panel
        if panel == CDS_PANEL_THYROID and any(k in name for k in ("tsh", "thyroid", "ft4", "ft3")):
            return panel
    if any(k in name for k in ("wbc", "rbc", "hemoglobin", "platelet", "cbc")):
        return CDS_PANEL_CBC
    if any(k in name for k in ("glucose", "sodium", "potassium", "chloride")):
        return CDS_PANEL_CHEMISTRY
    if any(k in name for k in ("urine", "urinalysis", "proteinuria")):
        return CDS_PANEL_URINALYSIS
    if any(k in name for k in ("pt", "inr", "aptt", "coag")):
        return CDS_PANEL_COAGULATION
    return CDS_PANEL_CHEMISTRY


class ClinicalRuleEngineService:

    @staticmethod
    def ensure_default_packs():
        if ClinicalGuidelinePack.query.first():
            return
        defaults = [
            ("PACK-CBC", "CBC Guideline Pack", CDS_PANEL_CBC),
            ("PACK-CHEM", "Chemistry Guideline Pack", CDS_PANEL_CHEMISTRY),
            ("PACK-LIVER", "Liver Panel Pack", CDS_PANEL_LIVER),
            ("PACK-KIDNEY", "Kidney Panel Pack", CDS_PANEL_KIDNEY),
            ("PACK-LIPID", "Lipid Panel Pack", CDS_PANEL_LIPID),
            ("PACK-HBA1C", "HbA1c Pack", CDS_PANEL_HBA1C),
            ("PACK-THY", "Thyroid Pack", CDS_PANEL_THYROID),
            ("PACK-UA", "Urinalysis Pack", CDS_PANEL_URINALYSIS),
            ("PACK-COAG", "Coagulation Pack", CDS_PANEL_COAGULATION),
        ]
        for code, name, panel in defaults:
            pack = ClinicalGuidelinePack(pack_code=code, name=name, panel_type=panel)
            db.session.add(pack)
            db.session.flush()
            db.session.add(
                ClinicalRuleDefinition(
                    rule_code=f"RULE-{code}",
                    pack_id=pack.id,
                    panel_type=panel,
                    condition_type="THRESHOLD",
                    finding_en=f"Abnormal finding in {panel} panel",
                    significance_en="Clinical correlation recommended",
                    confidence=0.85,
                )
            )
        db.session.commit()

    @staticmethod
    def list_reference_ranges(test_code=None, sex=None, age=None):
        rows = ReferenceRangeService.list_ranges(test_code=test_code, sex=sex)
        if age is not None:
            age = int(age)
            rows = [row for row in rows if row.age_min <= age <= row.age_max]
        return [row.to_dict() for row in rows]

    @staticmethod
    def evaluate_delta(patient_id, test_code, current_value, previous_value, threshold_percent=20):
        current = _parse_float(current_value)
        previous = _parse_float(previous_value)
        if current is None or previous is None or previous == 0:
            return None
        delta = abs((current - previous) / previous) * 100
        significant = delta >= threshold_percent
        row = ClinicalDeltaCheck(
            check_code=f"DLT-{uuid.uuid4().hex[:10].upper()}",
            patient_id=patient_id,
            test_code=test_code,
            current_value=current,
            previous_value=previous,
            delta_percent=round(delta, 2),
            is_significant=significant,
            message=f"Delta {delta:.1f}% for {test_code}" if significant else None,
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()


class AIInterpretationService:

    @staticmethod
    def interpret_payload(data):
        ClinicalRuleEngineService.ensure_default_packs()
        items = data.get("items") or []
        if not items and data.get("lab_result_id"):
            lab_items = LabResultItem.query.filter_by(lab_result_id=data["lab_result_id"]).all()
            items = [
                {
                    "test_code": item.test_code,
                    "test_name": item.test_name,
                    "result_value": item.result_value,
                    "unit": item.unit,
                    "reference_range": item.reference_range,
                }
                for item in lab_items
            ]
        if not items:
            raise CDSError("items or lab_result_id with result items is required", 400)

        patient_age = data.get("patient_age")
        patient_sex = data.get("patient_sex")
        interpretations = []
        for raw in items:
            item = LabResultItem(
                test_code=raw.get("test_code"),
                test_name=raw.get("test_name") or raw.get("test_code"),
                result_value=raw.get("result_value"),
                unit=raw.get("unit"),
                reference_range=raw.get("reference_range"),
            )
            panel = _detect_panel(item.test_code, item.test_name)
            interp = InterpretationEngine.interpret_item(item, patient_age, patient_sex)
            rules = ClinicalRuleDefinition.query.filter_by(panel_type=panel, is_active=True).all()
            supporting_rules = [rule.rule_code for rule in rules[:3]]
            abnormal = interp["flag"] not in ("NORMAL", "UNKNOWN")
            interpretations.append(
                {
                    "panel_type": panel,
                    "test_code": item.test_code,
                    "test_name": item.test_name,
                    "result_value": item.result_value,
                    "abnormal_findings": [interp["interpretation_en"]] if abnormal else [],
                    "explanation": interp["interpretation_en"],
                    "clinical_significance": rules[0].significance_en if rules else "Routine monitoring",
                    "confidence_score": rules[0].confidence if rules else 0.75,
                    "supporting_rules": supporting_rules,
                    "flag": interp["flag"],
                    "is_critical": interp["is_critical"],
                }
            )
        return {
            "count": len(interpretations),
            "interpretations": interpretations,
            "advisory_only": True,
        }


class AIRiskService:

    ALGORITHMS = {
        "diabetes": {"tests": ["GLU", "HBA1C"], "weight": {"GLU": 2, "HBA1C": 3}, "thresholds": {"GLU": 126, "HBA1C": 6.5}},
        "ckd": {"tests": ["CREA", "EGFR", "BUN"], "weight": {"CREA": 2, "EGFR": 3, "BUN": 1}, "thresholds": {"CREA": 1.5, "EGFR": 60, "BUN": 20}},
        "liver_disease": {"tests": ["ALT", "AST", "TBIL"], "weight": {"ALT": 2, "AST": 2, "TBIL": 3}, "thresholds": {"ALT": 40, "AST": 40, "TBIL": 1.2}},
        "cardiovascular": {"tests": ["CHOL", "LDL", "TG", "HDL"], "weight": {"CHOL": 1, "LDL": 2, "TG": 2, "HDL": 1}, "thresholds": {"CHOL": 200, "LDL": 130, "TG": 150, "HDL": 40}},
        "infection": {"tests": ["WBC", "CRP"], "weight": {"WBC": 2, "CRP": 3}, "thresholds": {"WBC": 11, "CRP": 10}},
    }

    @staticmethod
    def assess(data):
        items = data.get("items") or []
        values = {}
        for item in items:
            code = (item.get("test_code") or "").upper()
            val = _parse_float(item.get("result_value"))
            if code and val is not None:
                values[code] = val

        assessments = []
        for domain, cfg in AIRiskService.ALGORITHMS.items():
            score = 0
            factors = []
            for test_code, weight in cfg["weight"].items():
                if test_code not in values:
                    continue
                threshold = cfg["thresholds"].get(test_code, 0)
                if values[test_code] >= threshold:
                    score += weight
                    factors.append({"test_code": test_code, "value": values[test_code], "threshold": threshold})
            if not factors and domain != "infection":
                continue
            level = "LOW"
            if score >= 5:
                level = "HIGH"
            elif score >= 2:
                level = "MEDIUM"
            row = ClinicalRiskAssessment(
                assessment_code=f"RISK-{uuid.uuid4().hex[:10].upper()}",
                patient_id=data.get("patient_id"),
                lab_result_id=data.get("lab_result_id"),
                risk_domain=domain,
                risk_score=score,
                risk_level=level,
                algorithm=f"{domain}_v1",
                factors_json=json.dumps(factors),
            )
            db.session.add(row)
            assessments.append(row.to_dict())
        db.session.commit()
        return {"assessments": assessments, "advisory_only": True}


class AIRecommendationService:

    @staticmethod
    def generate(data):
        interp = AIInterpretationService.interpret_payload(data)
        recommendations = []
        for item in interp["interpretations"]:
            if not item["abnormal_findings"]:
                continue
            recs = []
            if item["is_critical"]:
                recs.append(
                    ClinicalRecommendation(
                        recommendation_code=f"REC-{uuid.uuid4().hex[:8].upper()}",
                        lab_result_id=data.get("lab_result_id"),
                        recommendation_type="URGENT_NOTIFY",
                        content="Advisory: notify treating physician immediately for critical value.",
                        specialty="Internal Medicine",
                        repeat_interval_days=1,
                        advisory_only=True,
                    )
                )
            if item["panel_type"] in (CDS_PANEL_LIPID, CDS_PANEL_HBA1C):
                recs.append(
                    ClinicalRecommendation(
                        recommendation_code=f"REC-{uuid.uuid4().hex[:8].upper()}",
                        lab_result_id=data.get("lab_result_id"),
                        recommendation_type="FOLLOW_UP_TEST",
                        content="Advisory: consider repeat fasting lipid panel in 3 months.",
                        specialty="Cardiology",
                        repeat_interval_days=90,
                        advisory_only=True,
                    )
                )
            if item["panel_type"] == CDS_PANEL_KIDNEY:
                recs.append(
                    ClinicalRecommendation(
                        recommendation_code=f"REC-{uuid.uuid4().hex[:8].upper()}",
                        lab_result_id=data.get("lab_result_id"),
                        recommendation_type="REFERRAL",
                        content="Advisory: nephrology referral may be appropriate if eGFR persistently reduced.",
                        specialty="Nephrology",
                        repeat_interval_days=30,
                        advisory_only=True,
                    )
                )
            recs.append(
                ClinicalRecommendation(
                    recommendation_code=f"REC-{uuid.uuid4().hex[:8].upper()}",
                    lab_result_id=data.get("lab_result_id"),
                    recommendation_type="LAB_COMMENT",
                    content="Advisory: verify specimen quality and pre-analytical factors.",
                    repeat_interval_days=7,
                    advisory_only=True,
                )
            )
            for rec in recs:
                db.session.add(rec)
                recommendations.append(rec.to_dict())
        db.session.commit()
        return {
            "count": len(recommendations),
            "recommendations": recommendations,
            "advisory_only": True,
        }


class CriticalDetectionService:

    @staticmethod
    def detect(data):
        items = data.get("items") or []
        patient_id = data.get("patient_id")
        lab_result_id = data.get("lab_result_id")
        alerts = []

        abnormal_markers = []
        for item in items:
            critical = CriticalValueService.evaluate(
                item.get("test_code"),
                item.get("result_value"),
                test_name=item.get("test_name"),
            )
            if critical.get("is_critical"):
                alert = CriticalAlertEvent(
                    alert_code=f"ALT-{uuid.uuid4().hex[:10].upper()}",
                    lab_result_id=lab_result_id,
                    patient_id=patient_id,
                    alert_type=CRITICAL_ALERT_PANIC,
                    severity="CRITICAL",
                    message=critical.get("message_en"),
                    markers_json=json.dumps([item.get("test_code")]),
                    notification_status="PENDING",
                )
                db.session.add(alert)
                alerts.append(alert)
            elif item.get("flag") in ("HIGH", "LOW", "CRITICAL"):
                abnormal_markers.append(item.get("test_code"))

            if item.get("previous_value"):
                delta = ClinicalRuleEngineService.evaluate_delta(
                    patient_id,
                    item.get("test_code"),
                    item.get("result_value"),
                    item.get("previous_value"),
                )
                if delta and delta.get("is_significant"):
                    alert = CriticalAlertEvent(
                        alert_code=f"ALT-{uuid.uuid4().hex[:10].upper()}",
                        lab_result_id=lab_result_id,
                        patient_id=patient_id,
                        alert_type=CRITICAL_ALERT_DELTA,
                        severity="HIGH",
                        message=delta.get("message"),
                        markers_json=json.dumps([item.get("test_code")]),
                    )
                    db.session.add(alert)
                    alerts.append(alert)

        if len(abnormal_markers) >= 2:
            alert = CriticalAlertEvent(
                alert_code=f"ALT-{uuid.uuid4().hex[:10].upper()}",
                lab_result_id=lab_result_id,
                patient_id=patient_id,
                alert_type=CRITICAL_ALERT_CORRELATION,
                severity="HIGH",
                message="Multiple correlated abnormal markers detected",
                markers_json=json.dumps(abnormal_markers),
            )
            db.session.add(alert)
            alerts.append(alert)

        if data.get("repeated_abnormality"):
            alert = CriticalAlertEvent(
                alert_code=f"ALT-{uuid.uuid4().hex[:10].upper()}",
                lab_result_id=lab_result_id,
                patient_id=patient_id,
                alert_type=CRITICAL_ALERT_REPEATED,
                severity="MEDIUM",
                message="Repeated abnormality pattern detected",
                markers_json=json.dumps(abnormal_markers),
            )
            db.session.add(alert)
            alerts.append(alert)

        db.session.commit()
        return {
            "count": len(alerts),
            "alerts": [alert.to_dict() for alert in alerts],
            "notification_events": [
                {"alert_code": alert.alert_code, "status": alert.notification_status}
                for alert in alerts
            ],
        }
