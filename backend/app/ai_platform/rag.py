"""RAG foundation — Release 3.0 Epic 9."""

from __future__ import annotations

import re
import uuid

from app.ai_platform.models import AIRagChunk, AIRagDocument
from app.extensions.db import db


class AIRagError(ValueError):
    pass


def _chunk_text(text: str, chunk_size: int = 400) -> list[str]:
    words = text.split()
    chunks = []
    current: list[str] = []
    length = 0
    for word in words:
        if length + len(word) + 1 > chunk_size and current:
            chunks.append(" ".join(current))
            current = [word]
            length = len(word)
        else:
            current.append(word)
            length += len(word) + 1
    if current:
        chunks.append(" ".join(current))
    return chunks


class AIRagService:
    @classmethod
    def ingest_document(
        cls,
        *,
        title: str,
        content: str,
        organization_id: str | None = None,
        source_type: str = "KNOWLEDGE",
    ) -> dict:
        if not title or not content:
            raise AIRagError("title and content required")
        doc = AIRagDocument(
            organization_id=organization_id,
            document_code=f"RAG-{uuid.uuid4().hex[:8].upper()}",
            title=title,
            source_type=source_type,
        )
        db.session.add(doc)
        db.session.flush()
        for idx, chunk in enumerate(_chunk_text(content)):
            db.session.add(
                AIRagChunk(
                    document_id=doc.id,
                    chunk_index=idx,
                    content=chunk,
                    token_estimate=max(1, len(chunk.split())),
                )
            )
        db.session.commit()
        return {**doc.to_dict(), "chunk_count": AIRagChunk.query.filter_by(document_id=doc.id).count()}

    @classmethod
    def retrieve(cls, query: str, *, organization_id: str | None = None, limit: int = 5) -> dict:
        if not query:
            raise AIRagError("query required")
        tokens = [t for t in re.split(r"\W+", query.lower()) if len(t) > 2]
        q = AIRagChunk.query.join(AIRagDocument, AIRagChunk.document_id == AIRagDocument.id)
        if organization_id:
            q = q.filter((AIRagDocument.organization_id == organization_id) | (AIRagDocument.organization_id.is_(None)))
        rows = q.limit(200).all()
        scored = []
        for row in rows:
            text = row.content.lower()
            score = sum(1 for t in tokens if t in text)
            if score:
                scored.append((score, row))
        scored.sort(key=lambda x: (-x[0], x[1].chunk_index))
        hits = [
            {
                "chunk_id": row.id,
                "document_id": row.document_id,
                "content": row.content,
                "score": score,
            }
            for score, row in scored[:limit]
        ]
        return {"query": query, "count": len(hits), "chunks": hits}
