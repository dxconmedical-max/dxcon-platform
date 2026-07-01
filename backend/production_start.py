#!/usr/bin/env python3
"""Production process entrypoint for API, worker, and scheduler roles."""

from __future__ import annotations

import os
import sys
import time


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


def _run_placeholder(role: str):
    print(f"DXCON {role} placeholder active — configure background jobs before GA")
    while True:
        time.sleep(3600)


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    role = (argv[0] if argv else os.getenv("DXCON_PROCESS_ROLE", "api")).lower()
    if role == "api":
        _run_api()
        return 0
    if role in {"worker", "scheduler"}:
        _run_placeholder(role)
        return 0
    print(f"Unknown role: {role}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
