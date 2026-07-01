from datetime import datetime
import uuid

from app.extensions.db import db


class MedicalKnowledge(db.Model):
    __tablename__ = "medical_knowledge"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    knowledge_code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100))
    content = db.Column(db.Text, nullable=False)
    tags_json = db.Column(db.Text, default="[]")
    evidence_level = db.Column(db.String(10), default="B")
    source_pack = db.Column(db.String(50))
    version = db.Column(db.String(20), default="1.0")
    citation_json = db.Column(db.Text, default="{}")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "knowledge_code": self.knowledge_code,
            "title": self.title,
            "category": self.category,
            "content": self.content,
            "tags_json": self.tags_json,
            "evidence_level": self.evidence_level,
            "source_pack": self.source_pack,
            "version": self.version,
            "citation_json": self.citation_json,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ClinicalGuideline(db.Model):
    __tablename__ = "clinical_guidelines"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    guideline_code = db.Column(db.String(50), unique=True, nullable=False)
    pack_source = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    version = db.Column(db.String(20), default="1.0")
    content = db.Column(db.Text, nullable=False)
    evidence_level = db.Column(db.String(10), default="B")
    citation_json = db.Column(db.Text, default="{}")
    test_codes_json = db.Column(db.Text, default="[]")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "guideline_code": self.guideline_code,
            "pack_source": self.pack_source,
            "title": self.title,
            "version": self.version,
            "content": self.content,
            "evidence_level": self.evidence_level,
            "citation_json": self.citation_json,
            "test_codes_json": self.test_codes_json,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DiseaseProfile(db.Model):
    __tablename__ = "disease_profiles"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    disease_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    icd10 = db.Column(db.String(20))
    description = db.Column(db.Text)
    test_codes_json = db.Column(db.Text, default="[]")
    pattern_json = db.Column(db.Text, default="{}")
    evidence_level = db.Column(db.String(10), default="B")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "disease_code": self.disease_code,
            "name": self.name,
            "icd10": self.icd10,
            "description": self.description,
            "test_codes_json": self.test_codes_json,
            "pattern_json": self.pattern_json,
            "evidence_level": self.evidence_level,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Biomarker(db.Model):
    __tablename__ = "biomarkers"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    biomarker_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    test_code = db.Column(db.String(50))
    unit = db.Column(db.String(50))
    related_biomarkers_json = db.Column(db.Text, default="[]")
    related_diseases_json = db.Column(db.Text, default="[]")
    evidence_level = db.Column(db.String(10), default="B")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "biomarker_code": self.biomarker_code,
            "name": self.name,
            "test_code": self.test_code,
            "unit": self.unit,
            "related_biomarkers_json": self.related_biomarkers_json,
            "related_diseases_json": self.related_diseases_json,
            "evidence_level": self.evidence_level,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ReferenceLibrary(db.Model):
    __tablename__ = "reference_libraries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_code = db.Column(db.String(50), unique=True, nullable=False)
    test_code = db.Column(db.String(50), nullable=False)
    test_name = db.Column(db.String(255))
    low_value = db.Column(db.Float)
    high_value = db.Column(db.Float)
    unit = db.Column(db.String(50))
    source_pack = db.Column(db.String(50))
    version = db.Column(db.String(20), default="1.0")
    citation_json = db.Column(db.Text, default="{}")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "reference_code": self.reference_code,
            "test_code": self.test_code,
            "test_name": self.test_name,
            "low_value": self.low_value,
            "high_value": self.high_value,
            "unit": self.unit,
            "source_pack": self.source_pack,
            "version": self.version,
            "citation_json": self.citation_json,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
