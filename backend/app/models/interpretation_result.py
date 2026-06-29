from datetime import datetime
import uuid

from app.extensions.db import db


class InterpretationResult(db.Model):

    __tablename__ = "interpretation_results"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    lab_result_id = db.Column(
        db.String(36),
        db.ForeignKey("lab_results.id"),
        nullable=False,
    )

    lab_result_item_id = db.Column(
        db.String(36),
        db.ForeignKey("lab_result_items.id"),
    )

    test_code = db.Column(db.String(50))

    test_name = db.Column(db.String(255))

    result_value = db.Column(db.String(255))

    flag = db.Column(db.String(20), default="NORMAL")

    reference_range_used = db.Column(db.String(255))

    is_critical = db.Column(db.Boolean, default=False)

    risk_level = db.Column(db.String(20), default="LOW")

    interpretation_en = db.Column(db.Text)

    interpretation_vi = db.Column(db.Text)

    recommendation_en = db.Column(db.Text)

    recommendation_vi = db.Column(db.Text)

    rule_id = db.Column(db.String(36), db.ForeignKey("interpretation_rules.id"))

    template_code = db.Column(db.String(50))

    template_version = db.Column(db.Integer)

    metadata_json = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, language=None):
        payload = {
            "id": self.id,
            "lab_result_id": self.lab_result_id,
            "lab_result_item_id": self.lab_result_item_id,
            "test_code": self.test_code,
            "test_name": self.test_name,
            "result_value": self.result_value,
            "flag": self.flag,
            "reference_range_used": self.reference_range_used,
            "is_critical": self.is_critical,
            "risk_level": self.risk_level,
            "interpretation_en": self.interpretation_en,
            "interpretation_vi": self.interpretation_vi,
            "recommendation_en": self.recommendation_en,
            "recommendation_vi": self.recommendation_vi,
            "rule_id": self.rule_id,
            "template_code": self.template_code,
            "template_version": self.template_version,
            "metadata_json": self.metadata_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if language == "vi":
            payload["interpretation"] = self.interpretation_vi
            payload["recommendation"] = self.recommendation_vi
        else:
            payload["interpretation"] = self.interpretation_en
            payload["recommendation"] = self.recommendation_en
        return payload
