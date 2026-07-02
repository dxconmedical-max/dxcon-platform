import json
import uuid

from app.ai_platform.models import PromptTemplate, PromptVersion
from app.extensions.db import db


class PromptRegistry:
    DEFAULT_PROMPTS = (
        ("PROMPT-INTERPRET", "Result Interpretation", "interpretation", "Summarize lab findings for clinician review only. Do not diagnose."),
        ("PROMPT-SUMMARY", "Clinical Summary", "summary", "Provide an advisory summary requiring human review."),
    )

    @classmethod
    def ensure_defaults(cls):
        if PromptTemplate.query.first():
            return {"seeded": False}
        for code, name, task_type, template_text in cls.DEFAULT_PROMPTS:
            prompt = PromptTemplate(
                prompt_code=code,
                name=name,
                task_type=task_type,
                active_version=1,
            )
            db.session.add(prompt)
            db.session.flush()
            db.session.add(
                PromptVersion(
                    prompt_id=prompt.id,
                    version=1,
                    template_text=template_text,
                    metadata_json=json.dumps({"author": "system", "status": "active"}),
                )
            )
        db.session.commit()
        return {"seeded": True}

    @classmethod
    def list_prompts(cls):
        cls.ensure_defaults()
        rows = PromptTemplate.query.order_by(PromptTemplate.created_at.desc()).all()
        return {"count": len(rows), "prompts": [row.to_dict() for row in rows]}

    @classmethod
    def register(cls, data):
        prompt_code = data.get("prompt_code") or f"PROMPT-{uuid.uuid4().hex[:8].upper()}"
        existing = PromptTemplate.query.filter_by(prompt_code=prompt_code).first()
        template_text = data.get("template_text")
        if not template_text:
            raise ValueError("template_text is required")

        if existing:
            next_version = (existing.active_version or 0) + 1
            existing.active_version = next_version
            version_row = PromptVersion(
                prompt_id=existing.id,
                version=next_version,
                template_text=template_text,
                metadata_json=json.dumps(data.get("metadata") or {}),
            )
            db.session.add(version_row)
            db.session.commit()
            return {
                "prompt": existing.to_dict(),
                "version": version_row.to_dict(),
                "versioned": True,
            }

        prompt = PromptTemplate(
            prompt_code=prompt_code,
            name=data.get("name") or prompt_code,
            task_type=data.get("task_type") or "general",
            active_version=1,
        )
        db.session.add(prompt)
        db.session.flush()
        version_row = PromptVersion(
            prompt_id=prompt.id,
            version=1,
            template_text=template_text,
            metadata_json=json.dumps(data.get("metadata") or {}),
        )
        db.session.add(version_row)
        db.session.commit()
        return {"prompt": prompt.to_dict(), "version": version_row.to_dict(), "versioned": False}

    @classmethod
    def get_active_version(cls, prompt_id):
        prompt = PromptTemplate.query.filter_by(id=prompt_id).first()
        if prompt is None:
            raise KeyError("Prompt not found")
        version = PromptVersion.query.filter_by(prompt_id=prompt_id, version=prompt.active_version).first()
        if version is None:
            raise KeyError("Active prompt version not found")
        return prompt, version

    @classmethod
    def get_by_code(cls, prompt_code):
        cls.ensure_defaults()
        prompt = PromptTemplate.query.filter_by(prompt_code=prompt_code).first()
        if prompt is None:
            raise KeyError("Prompt not found")
        return cls.get_active_version(prompt.id)
