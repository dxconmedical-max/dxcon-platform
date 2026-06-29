import json
import uuid

from app.core.statuses import (
    CRITICAL_RULE_ACTIVE,
    INTERPRETATION_FLAG_CRITICAL,
    INTERPRETATION_FLAG_HIGH,
    INTERPRETATION_FLAG_LOW,
    INTERPRETATION_FLAG_NORMAL,
    INTERPRETATION_LANG_EN,
    INTERPRETATION_LANG_VI,
    INTERPRETATION_RISK_CRITICAL,
    INTERPRETATION_RISK_HIGH,
    INTERPRETATION_RISK_LOW,
    INTERPRETATION_RISK_MEDIUM,
    INTERPRETATION_RULE_ACTIVE,
    INTERPRETATION_TEMPLATE_ACTIVE,
    REFERENCE_RANGE_ACTIVE,
)
from app.extensions.db import db
from app.models.critical_value_rule import CriticalValueRule
from app.models.interpretation_result import InterpretationResult
from app.models.interpretation_rule import InterpretationRule
from app.models.interpretation_template import InterpretationTemplate
from app.models.lab_result import LabResult
from app.models.lab_result_item import LabResultItem
from app.models.reference_range import ReferenceRange
from app.services.result_flag import calculate_result_flag


class InterpretationError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _parse_float(value):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


class ReferenceRangeService:

    @staticmethod
    def list_ranges(test_code=None, sex=None, status=REFERENCE_RANGE_ACTIVE):
        query = ReferenceRange.query.filter(ReferenceRange.status == status)
        if test_code:
            query = query.filter(ReferenceRange.test_code == test_code)
        if sex:
            query = query.filter(ReferenceRange.sex.in_([sex, "ALL"]))
        return query.order_by(ReferenceRange.test_code.asc()).all()

    @staticmethod
    def resolve(test_code, test_name=None, age=None, sex=None):
        age = 0 if age is None else int(age)
        sex = (sex or "ALL").upper()
        query = ReferenceRange.query.filter(
            ReferenceRange.status == REFERENCE_RANGE_ACTIVE,
            ReferenceRange.age_min <= age,
            ReferenceRange.age_max >= age,
        )
        if test_code:
            query = query.filter(ReferenceRange.test_code == test_code)
        elif test_name:
            query = query.filter(ReferenceRange.test_name.ilike(f"%{test_name}%"))
        else:
            return None

        candidates = query.all()
        filtered = [
            row
            for row in candidates
            if row.sex in (sex, "ALL")
        ]
        if not filtered and candidates:
            filtered = candidates
        if not filtered:
            return None
        filtered.sort(key=lambda row: (0 if row.sex == sex else 1, row.age_max - row.age_min))
        return filtered[0]


class CriticalValueService:

    @staticmethod
    def list_rules(test_code=None):
        query = CriticalValueRule.query.filter(
            CriticalValueRule.status == CRITICAL_RULE_ACTIVE
        )
        if test_code:
            query = query.filter(CriticalValueRule.test_code == test_code)
        return query.order_by(CriticalValueRule.test_code.asc()).all()

    @staticmethod
    def evaluate(test_code, result_value, test_name=None):
        numeric = _parse_float(result_value)
        if numeric is None:
            return {
                "is_critical": False,
                "severity": None,
                "message_en": None,
                "message_vi": None,
                "rule": None,
            }

        query = CriticalValueRule.query.filter(
            CriticalValueRule.status == CRITICAL_RULE_ACTIVE
        )
        if test_code:
            query = query.filter(CriticalValueRule.test_code == test_code)
        rules = query.all()
        if not rules and test_name:
            rules = CriticalValueRule.query.filter(
                CriticalValueRule.status == CRITICAL_RULE_ACTIVE,
                CriticalValueRule.test_name.ilike(f"%{test_name}%"),
            ).all()

        for rule in rules:
            if rule.panic_low is not None and numeric <= rule.panic_low:
                return {
                    "is_critical": True,
                    "severity": rule.severity or INTERPRETATION_RISK_CRITICAL,
                    "message_en": rule.message_en,
                    "message_vi": rule.message_vi,
                    "rule": rule,
                }
            if rule.panic_high is not None and numeric >= rule.panic_high:
                return {
                    "is_critical": True,
                    "severity": rule.severity or INTERPRETATION_RISK_CRITICAL,
                    "message_en": rule.message_en,
                    "message_vi": rule.message_vi,
                    "rule": rule,
                }

        return {
            "is_critical": False,
            "severity": None,
            "message_en": None,
            "message_vi": None,
            "rule": None,
        }


class RecommendationService:

    @staticmethod
    def generate(flag, risk_level, critical_payload=None, rule=None, language=INTERPRETATION_LANG_EN):
        if rule:
            if language == INTERPRETATION_LANG_VI:
                if rule.recommendation_vi:
                    return rule.recommendation_vi
                return rule.recommendation_en
            return rule.recommendation_en or rule.recommendation_vi

        if critical_payload and critical_payload.get("is_critical"):
            if language == INTERPRETATION_LANG_VI:
                return critical_payload.get("message_vi") or "Can thong bao bac si ngay lap tuc va xu tri cap cuu neu can."
            return critical_payload.get("message_en") or "Notify physician immediately and manage as a critical value."

        if flag == INTERPRETATION_FLAG_HIGH:
            if language == INTERPRETATION_LANG_VI:
                return "Ket qua cao hon khoang tham chieu. Can danh gia lam sang va theo doi."
            return "Result is above reference range. Recommend clinical correlation and follow-up."

        if flag == INTERPRETATION_FLAG_LOW:
            if language == INTERPRETATION_LANG_VI:
                return "Ket qua thap hon khoang tham chieu. Can danh gia lam sang va theo doi."
            return "Result is below reference range. Recommend clinical correlation and follow-up."

        if language == INTERPRETATION_LANG_VI:
            return "Tiep tuc theo doi dinh ky."
        return "Continue routine monitoring."


class InterpretationEngine:

    @staticmethod
    def list_rules():
        return (
            InterpretationRule.query.filter(
                InterpretationRule.status == INTERPRETATION_RULE_ACTIVE
            )
            .order_by(InterpretationRule.priority.asc())
            .all()
        )

    @staticmethod
    def list_templates(template_code=None):
        query = InterpretationTemplate.query.filter(
            InterpretationTemplate.status == INTERPRETATION_TEMPLATE_ACTIVE
        )
        if template_code:
            query = query.filter(InterpretationTemplate.template_code == template_code)
        return query.order_by(
            InterpretationTemplate.template_code.asc(),
            InterpretationTemplate.version.desc(),
        ).all()

    @staticmethod
    def _match_rule(item, flag):
        rules = InterpretationEngine.list_rules()
        test_code = (item.test_code or "").upper()
        test_name = (item.test_name or "").lower()
        matched = []
        for rule in rules:
            if rule.test_code and rule.test_code.upper() != test_code:
                continue
            if rule.test_name_pattern and rule.test_name_pattern.lower() not in test_name:
                continue
            if rule.condition_flag not in ("ANY", flag):
                continue
            matched.append(rule)
        if not matched:
            return None
        matched.sort(key=lambda row: row.priority)
        return matched[0]

    @staticmethod
    def _resolve_template(template_code, language=INTERPRETATION_LANG_EN):
        template = (
            InterpretationTemplate.query.filter_by(
                template_code=template_code,
                language=language,
                status=INTERPRETATION_TEMPLATE_ACTIVE,
            )
            .order_by(InterpretationTemplate.version.desc())
            .first()
        )
        if template:
            return template
        return (
            InterpretationTemplate.query.filter_by(
                template_code=template_code,
                language=INTERPRETATION_LANG_EN,
                status=INTERPRETATION_TEMPLATE_ACTIVE,
            )
            .order_by(InterpretationTemplate.version.desc())
            .first()
        )

    @staticmethod
    def _render_template(template, context):
        body = template.body_template or ""
        for key, value in context.items():
            body = body.replace(f"{{{key}}}", str(value or ""))
        return body

    @staticmethod
    def _build_finding(item, flag, reference_range, critical_payload, rule):
        if rule:
            finding_en = rule.finding_en or f"{item.test_name} flagged as {flag}."
            finding_vi = rule.finding_vi or finding_en
        elif critical_payload.get("is_critical"):
            finding_en = critical_payload.get("message_en") or f"{item.test_name} is a critical value."
            finding_vi = critical_payload.get("message_vi") or finding_en
        elif flag == INTERPRETATION_FLAG_HIGH:
            finding_en = f"{item.test_name} is above the reference range ({reference_range})."
            finding_vi = f"{item.test_name} cao hon khoang tham chieu ({reference_range})."
        elif flag == INTERPRETATION_FLAG_LOW:
            finding_en = f"{item.test_name} is below the reference range ({reference_range})."
            finding_vi = f"{item.test_name} thap hon khoang tham chieu ({reference_range})."
        else:
            finding_en = f"{item.test_name} is within the reference range ({reference_range})."
            finding_vi = f"{item.test_name} nam trong khoang tham chieu ({reference_range})."
        return finding_en, finding_vi

    @staticmethod
    def _determine_flag(item, reference_row):
        reference_text = item.reference_range
        if reference_row:
            reference_text = reference_row.as_range_text()
        flag = calculate_result_flag(item.result_value, reference_text)
        if flag in ("HIGH", "LOW"):
            return flag, reference_text
        if flag == "UNKNOWN" and reference_row:
            numeric = _parse_float(item.result_value)
            if numeric is not None:
                if reference_row.low_value is not None and numeric < reference_row.low_value:
                    return INTERPRETATION_FLAG_LOW, reference_text
                if reference_row.high_value is not None and numeric > reference_row.high_value:
                    return INTERPRETATION_FLAG_HIGH, reference_text
        return INTERPRETATION_FLAG_NORMAL, reference_text

    @staticmethod
    def interpret_item(item, patient_age=None, patient_sex=None):
        reference_row = ReferenceRangeService.resolve(
            item.test_code,
            test_name=item.test_name,
            age=patient_age,
            sex=patient_sex,
        )
        flag, reference_text = InterpretationEngine._determine_flag(item, reference_row)
        critical_payload = CriticalValueService.evaluate(
            item.test_code,
            item.result_value,
            test_name=item.test_name,
        )
        if critical_payload.get("is_critical"):
            flag = INTERPRETATION_FLAG_CRITICAL

        rule = InterpretationEngine._match_rule(item, flag)
        risk_level = INTERPRETATION_RISK_LOW
        if rule:
            risk_level = rule.risk_level or INTERPRETATION_RISK_LOW
        elif critical_payload.get("is_critical"):
            risk_level = critical_payload.get("severity") or INTERPRETATION_RISK_CRITICAL
        elif flag in (INTERPRETATION_FLAG_HIGH, INTERPRETATION_FLAG_LOW):
            risk_level = INTERPRETATION_RISK_MEDIUM

        finding_en, finding_vi = InterpretationEngine._build_finding(
            item,
            flag,
            reference_text,
            critical_payload,
            rule,
        )

        template = InterpretationEngine._resolve_template("GENERAL_FINDING", INTERPRETATION_LANG_EN)
        template_context = {
            "test_name": item.test_name,
            "result_value": item.result_value,
            "flag": flag,
            "reference_range": reference_text,
        }
        if template:
            rendered = InterpretationEngine._render_template(template, template_context)
            if template.language == INTERPRETATION_LANG_VI:
                finding_vi = rendered
            else:
                finding_en = rendered

        recommendation_en = RecommendationService.generate(
            flag,
            risk_level,
            critical_payload,
            rule,
            INTERPRETATION_LANG_EN,
        )
        recommendation_vi = RecommendationService.generate(
            flag,
            risk_level,
            critical_payload,
            rule,
            INTERPRETATION_LANG_VI,
        )

        return {
            "lab_result_item_id": item.id,
            "test_code": item.test_code,
            "test_name": item.test_name,
            "result_value": item.result_value,
            "flag": flag,
            "reference_range_used": reference_text,
            "is_critical": critical_payload.get("is_critical", False),
            "risk_level": risk_level,
            "interpretation_en": finding_en,
            "interpretation_vi": finding_vi,
            "recommendation_en": recommendation_en,
            "recommendation_vi": recommendation_vi,
            "rule_id": rule.id if rule else None,
            "template_code": template.template_code if template else None,
            "template_version": template.version if template else None,
            "metadata_json": json.dumps(
                {
                    "reference_range_id": reference_row.id if reference_row else None,
                    "critical_rule_id": critical_payload["rule"].id
                    if critical_payload.get("rule")
                    else None,
                }
            ),
        }

    @staticmethod
    def run(lab_result_id, patient_age=None, patient_sex=None, replace_existing=True):
        lab_result = LabResult.query.get(lab_result_id)
        if not lab_result:
            raise InterpretationError("Lab result not found", 404)

        items = LabResultItem.query.filter_by(lab_result_id=lab_result.id).all()
        if not items:
            raise InterpretationError("Lab result has no items to interpret", 400)

        if replace_existing:
            InterpretationResult.query.filter_by(lab_result_id=lab_result.id).delete()

        saved = []
        for item in items:
            payload = InterpretationEngine.interpret_item(
                item,
                patient_age=patient_age,
                patient_sex=patient_sex,
            )
            row = InterpretationResult(
                lab_result_id=lab_result.id,
                **payload,
            )
            db.session.add(row)
            saved.append(row)

        db.session.commit()
        return saved

    @staticmethod
    def get_for_result(lab_result_id, language=None):
        lab_result = LabResult.query.get(lab_result_id)
        if not lab_result:
            raise InterpretationError("Lab result not found", 404)
        rows = (
            InterpretationResult.query.filter_by(lab_result_id=lab_result_id)
            .order_by(InterpretationResult.created_at.desc())
            .all()
        )
        return {
            "lab_result_id": lab_result_id,
            "result_code": lab_result.result_code,
            "count": len(rows),
            "interpretations": [row.to_dict(language=language) for row in rows],
        }
