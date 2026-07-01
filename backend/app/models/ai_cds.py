from datetime import datetime
import uuid

from app.extensions.db import db


class ClinicalGuidelinePack(db.Model):
    __tablename__ = "clinical_guideline_packs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    pack_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    panel_type = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(20), default="1.0")
    rules_json = db.Column(db.Text, default="[]")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "pack_code": self.pack_code,
            "name": self.name,
            "panel_type": self.panel_type,
            "version": self.version,
            "rules_json": self.rules_json,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ClinicalRuleDefinition(db.Model):
    __tablename__ = "clinical_rule_definitions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_code = db.Column(db.String(50), unique=True, nullable=False)
    pack_id = db.Column(db.String(36), db.ForeignKey("clinical_guideline_packs.id"))
    test_code = db.Column(db.String(50))
    panel_type = db.Column(db.String(50))
    condition_type = db.Column(db.String(50), default="THRESHOLD")
    sex = db.Column(db.String(10), default="ALL")
    age_min = db.Column(db.Integer, default=0)
    age_max = db.Column(db.Integer, default=120)
    threshold_low = db.Column(db.Float)
    threshold_high = db.Column(db.Float)
    delta_percent = db.Column(db.Float)
    finding_en = db.Column(db.Text)
    significance_en = db.Column(db.Text)
    confidence = db.Column(db.Float, default=0.8)
    priority = db.Column(db.Integer, default=100)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "pack_id": self.pack_id,
            "test_code": self.test_code,
            "panel_type": self.panel_type,
            "condition_type": self.condition_type,
            "sex": self.sex,
            "age_min": self.age_min,
            "age_max": self.age_max,
            "threshold_low": self.threshold_low,
            "threshold_high": self.threshold_high,
            "delta_percent": self.delta_percent,
            "finding_en": self.finding_en,
            "significance_en": self.significance_en,
            "confidence": self.confidence,
            "priority": self.priority,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ClinicalDeltaCheck(db.Model):
    __tablename__ = "clinical_delta_checks"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    check_code = db.Column(db.String(50), unique=True, nullable=False)
    patient_id = db.Column(db.String(36))
    test_code = db.Column(db.String(50), nullable=False)
    current_value = db.Column(db.Float)
    previous_value = db.Column(db.Float)
    delta_percent = db.Column(db.Float)
    is_significant = db.Column(db.Boolean, default=False)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "check_code": self.check_code,
            "patient_id": self.patient_id,
            "test_code": self.test_code,
            "current_value": self.current_value,
            "previous_value": self.previous_value,
            "delta_percent": self.delta_percent,
            "is_significant": self.is_significant,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ClinicalRiskAssessment(db.Model):
    __tablename__ = "clinical_risk_assessments"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    assessment_code = db.Column(db.String(50), unique=True, nullable=False)
    patient_id = db.Column(db.String(36))
    lab_result_id = db.Column(db.String(36))
    risk_domain = db.Column(db.String(50), nullable=False)
    risk_score = db.Column(db.Float, default=0)
    risk_level = db.Column(db.String(20), default="LOW")
    algorithm = db.Column(db.String(50))
    factors_json = db.Column(db.Text, default="[]")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "assessment_code": self.assessment_code,
            "patient_id": self.patient_id,
            "lab_result_id": self.lab_result_id,
            "risk_domain": self.risk_domain,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "algorithm": self.algorithm,
            "factors_json": self.factors_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ClinicalRecommendation(db.Model):
    __tablename__ = "clinical_recommendations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    recommendation_code = db.Column(db.String(50), unique=True, nullable=False)
    lab_result_id = db.Column(db.String(36))
    recommendation_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    specialty = db.Column(db.String(100))
    repeat_interval_days = db.Column(db.Integer)
    advisory_only = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "recommendation_code": self.recommendation_code,
            "lab_result_id": self.lab_result_id,
            "recommendation_type": self.recommendation_type,
            "content": self.content,
            "specialty": self.specialty,
            "repeat_interval_days": self.repeat_interval_days,
            "advisory_only": bool(self.advisory_only),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CriticalAlertEvent(db.Model):
    __tablename__ = "critical_alert_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_code = db.Column(db.String(50), unique=True, nullable=False)
    lab_result_id = db.Column(db.String(36))
    patient_id = db.Column(db.String(36))
    alert_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), default="CRITICAL")
    message = db.Column(db.Text)
    markers_json = db.Column(db.Text, default="[]")
    notification_status = db.Column(db.String(50), default="PENDING")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "alert_code": self.alert_code,
            "lab_result_id": self.lab_result_id,
            "patient_id": self.patient_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "markers_json": self.markers_json,
            "notification_status": self.notification_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
