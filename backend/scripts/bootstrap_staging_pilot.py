#!/usr/bin/env python3
"""Bootstrap deterministic non-PHI staging pilot accounts.

Refuses APP_ENV=production.
Does not print plaintext passwords after creation.
Passwords are read from environment variables only.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import string
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REPORT_PATH = ROOT.parent / "generated-release" / "STAGING_BOOTSTRAP_REPORT.json"

# Minimal deterministic staging roles for UAT.
STAGING_ACCOUNTS = [
    {"key": "super_admin", "email_env": "STAGING_ADMIN_EMAIL", "password_env": "STAGING_ADMIN_PASSWORD", "role": "SUPER_ADMIN", "default_email": "admin@staging.dxcon.local"},
    {"key": "reception", "email_env": "STAGING_RECEPTION_EMAIL", "password_env": "STAGING_RECEPTION_PASSWORD", "role": "RECEPTION", "default_email": "reception@staging.dxcon.local"},
    {"key": "collector", "email_env": "STAGING_COLLECTOR_EMAIL", "password_env": "STAGING_COLLECTOR_PASSWORD", "role": "COLLECTOR", "default_email": "collector@staging.dxcon.local"},
    {"key": "lab_technician", "email_env": "STAGING_LAB_EMAIL", "password_env": "STAGING_LAB_PASSWORD", "role": "LAB", "default_email": "lab@staging.dxcon.local"},
    {"key": "doctor", "email_env": "STAGING_DOCTOR_EMAIL", "password_env": "STAGING_DOCTOR_PASSWORD", "role": "DOCTOR", "default_email": "doctor@staging.dxcon.local"},
    {"key": "clinic", "email_env": "STAGING_CLINIC_EMAIL", "password_env": "STAGING_CLINIC_PASSWORD", "role": "CLINIC", "default_email": "clinic@staging.dxcon.local"},
    {"key": "patient", "email_env": "STAGING_PATIENT_EMAIL", "password_env": "STAGING_PATIENT_PASSWORD", "role": "PATIENT", "default_email": "patient@staging.dxcon.local"},
]


def _generate_password(length: int = 20) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap staging pilot accounts")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--generate-missing-passwords",
        action="store_true",
        help="One-time: generate passwords for missing env vars and print them once",
    )
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("Specify --dry-run or --apply", file=sys.stderr)
        return 2

    app_env = (os.getenv("APP_ENV") or "").strip().lower()
    if app_env in {"production", "prod", "live"}:
        print("FAIL: refusing to run against production APP_ENV", file=sys.stderr)
        return 1
    if app_env and app_env not in {"staging", "stage", "uat", "development", "testing", "test", "ci"}:
        print(f"FAIL: unexpected APP_ENV={app_env!r}; expected staging or local test", file=sys.stderr)
        return 1

    if not os.getenv("DATABASE_URL"):
        print("FAIL: DATABASE_URL is required", file=sys.stderr)
        return 1

    from app import create_app
    from app.core.passwords import hash_password
    from app.extensions.db import db
    from app.models.user import User

    app = create_app()
    results = []
    generated: dict[str, str] = {}

    with app.app_context():
        for spec in STAGING_ACCOUNTS:
            email = (os.getenv(spec["email_env"]) or "").strip() or spec["default_email"]
            password = (os.getenv(spec["password_env"]) or "").strip()
            entry = {
                "key": spec["key"],
                "role": spec["role"],
                "email": email,
                "action": "skip",
            }

            existing = User.query.filter_by(email=email).first()
            if existing:
                entry["action"] = "exists"
                entry["user_id"] = existing.id
                results.append(entry)
                continue

            if args.dry_run:
                entry["action"] = "would_create"
                entry["password_ready"] = bool(password) or args.generate_missing_passwords
                results.append(entry)
                continue

            if not password:
                if not args.generate_missing_passwords:
                    entry["action"] = "blocked"
                    entry["reason"] = f"Missing {spec['password_env']}"
                    results.append(entry)
                    continue
                password = _generate_password()
                generated[spec["password_env"]] = password

            user = User(
                email=email,
                role=spec["role"],
                password_hash=hash_password(password),
                is_active=True,
            )
            db.session.add(user)
            entry["action"] = "created"
            results.append(entry)

        if args.apply:
            db.session.commit()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "dry-run" if args.dry_run else "apply",
        "app_env": app_env or "(unset)",
        "accounts": results,
        "passwords_printed": bool(generated),
        "note": "Synthetic staging accounts only. No real PHI.",
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

    if generated:
        print("\nONE-TIME GENERATED PASSWORDS (store in vault, then clear terminal):", file=sys.stderr)
        for key, value in generated.items():
            print(f"  {key}={value}", file=sys.stderr)

    failed = any(r.get("action") == "blocked" for r in results)
    return 1 if failed and args.apply else 0


if __name__ == "__main__":
    raise SystemExit(main())
