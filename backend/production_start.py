#!/usr/bin/env python3
"""Production process entrypoint for API, worker, and scheduler roles."""

from __future__ import annotations

import os
import sys


def _run_api():
    os.execvp(
        "gunicorn",
        [
            "gunicorn",
            "-c",
            "gunicorn.conf.py",
            "run:app",
        ],
    )


def _create_app():
    from app import create_app

    return create_app()


def _run_worker():
    from app.operations.process_runtime import run_worker_loop

    run_worker_loop(_create_app())


def _run_scheduler():
    from app.operations.process_runtime import run_scheduler_loop

    run_scheduler_loop(_create_app())


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    role = (argv[0] if argv else os.getenv("DXCON_PROCESS_ROLE", "api")).lower()
    if role == "api":
        _run_api()
        return 0
    if role == "worker":
        _run_worker()
        return 0
    if role == "scheduler":
        _run_scheduler()
        return 0
    print(f"Unknown role: {role}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
