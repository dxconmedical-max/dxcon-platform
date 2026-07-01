from flask import current_app

from app.core.db_pool import pool_status
from app.core.monitoring import application_metrics


class ScalingAdvisor:
    @staticmethod
    def recommend(app=None):
        app = app or current_app._get_current_object()
        metrics = application_metrics(app)
        queue_depth = metrics.get("queue", {}).get("pending", 0) or metrics.get("queue", {}).get("size", 0)
        pool = pool_status(app)
        workers = int(app.config.get("WEB_CONCURRENCY", 2))

        worker_rec = workers
        if queue_depth > 100:
            worker_rec = min(workers + 2, 8)
        elif queue_depth < 10 and workers > 2:
            worker_rec = max(workers - 1, 2)

        pool_size = pool.get("pool_size") or app.config.get("DB_POOL_SIZE", 5)
        pool_rec = pool_size
        if worker_rec > workers:
            pool_rec = min(pool_size + 2, 20)

        return {
            "workers": {
                "current": workers,
                "recommended": worker_rec,
                "reason": "queue_depth" if queue_depth > 100 else "baseline",
            },
            "database_pool": {
                "current": pool_size,
                "recommended": pool_rec,
                "overflow": pool.get("overflow", app.config.get("DB_MAX_OVERFLOW", 10)),
            },
            "queue": {
                "depth": queue_depth,
                "recommendation": "scale_workers" if queue_depth > 100 else "stable",
            },
            "cache": {
                "redis_configured": bool(app.config.get("REDIS_URL")),
                "recommendation": "enable_redis" if not app.config.get("REDIS_URL") else "ok",
            },
        }
