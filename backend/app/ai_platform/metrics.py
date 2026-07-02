from datetime import datetime

from app.ai_platform.models import AIUsageMetric
from app.extensions.db import db


class AIUsageMetricsService:
    @staticmethod
    def record(provider_id, task_type, tokens_in=0, tokens_out=0, requests=1):
        row = AIUsageMetric(
            provider_id=provider_id,
            task_type=task_type,
            tokens_in=int(tokens_in or 0),
            tokens_out=int(tokens_out or 0),
            requests=int(requests or 1),
        )
        db.session.add(row)
        db.session.commit()
        return row.to_dict()

    @staticmethod
    def summary():
        rows = AIUsageMetric.query.all()
        totals = {
            "requests": sum(row.requests for row in rows),
            "tokens_in": sum(row.tokens_in for row in rows),
            "tokens_out": sum(row.tokens_out for row in rows),
            "by_task_type": {},
        }
        for row in rows:
            bucket = totals["by_task_type"].setdefault(
                row.task_type,
                {"requests": 0, "tokens_in": 0, "tokens_out": 0},
            )
            bucket["requests"] += row.requests
            bucket["tokens_in"] += row.tokens_in
            bucket["tokens_out"] += row.tokens_out
        return {"count": len(rows), "totals": totals, "metrics": [row.to_dict() for row in rows[-20:]]}
