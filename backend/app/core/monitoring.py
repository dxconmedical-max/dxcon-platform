import logging
import os
import resource

from app.core.background_tasks import background_tasks
from app.core.build_info import build_info
from app.core.db_pool import pool_status
from app.core.metrics import metrics
from app.core.performance_metrics import performance_metrics

logger = logging.getLogger("dxcon.monitoring")


def _memory_usage_mb():
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if os.uname().sysname == "Darwin":
        return round(usage / (1024 * 1024), 2)
    return round(usage / 1024, 2)


def _cpu_load():
    try:
        load1, load5, load15 = os.getloadavg()
        return {
            "load_1m": round(load1, 2),
            "load_5m": round(load5, 2),
            "load_15m": round(load15, 2),
        }
    except (AttributeError, OSError):
        return {"load_1m": None, "load_5m": None, "load_15m": None}


def application_metrics(app):
    return {
        "requests": metrics.snapshot(),
        "performance": performance_metrics.snapshot(app),
        "memory_mb": _memory_usage_mb(),
        "cpu": _cpu_load(),
        "database": pool_status(app),
        "queue": background_tasks.snapshot(),
        "build": build_info(),
    }
