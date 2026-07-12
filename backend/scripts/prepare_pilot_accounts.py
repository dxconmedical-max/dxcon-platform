#!/usr/bin/env python3
"""Idempotent pilot account preparation — never run automatically against production."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REPORT_PATH = ROOT / "generated_release" / "PILOT_ACCOUNT_PREP_REPORT.json"

PILOT_ACCOUNTS = [
    {"key": "dxcon_admin", "email_env": "PILOT_ADMIN_EMAIL", "password_env": "PILOT_ADMIN_PASSWORD", "role": "SUPER_ADMIN"},
    {"key": "clinic_owner", "email_env": "PILOT_CLINIC_OWNER_EMAIL", "password_env": "PILOT_CLINIC_OWNER_PASSWORD", "role": "CLINIC_OWNER"},
    {"key": "partner_doctor", "email_env": "PILOT_DOCTOR_EMAIL", "password_env": "PILOT_DOCTOR_PASSWORD", "role": "DOCTOR"},
    {"key": "lab_manager", "email_env": "PILOT_LAB_MANAGER_EMAIL", "password_env": "PILOT_LAB_MANAGER_PASSWORD", "role": "LAB_MANAGER"},
    {"key": "collector", "email_env": "PILOT_COLLECTOR_EMAIL", "password_env": "PILOT_COLLECTOR_PASSWORD", "role": "COLLECTOR"},
    {"key": "patient", "email_env": "PILOT_PATIENT_EMAIL", "password_env": "PILOT_PATIENT_PASSWORD", "role": "PATIENT"},
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or verify DxCon pilot accounts")
    parser.add_argument("--dry-run", action="store_true", help="Plan only; no database writes")
    parser.add_argument("--apply", action="store_true", help="Create missing accounts when env passwords are set")
    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("Specify --dry-run or --apply", file=sys.stderr)
        return 2

    if os.getenv("APP_ENV") == "production" and args.apply:
        print("FAIL: Refusing --apply when APP_ENV=production. Use staging or local.", file=sys.stderr)
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

    with app.app_context():
        for spec in PILOT_ACCOUNTS:
            email = os.getenv(spec["email_env"], "").strip()
            password = os.getenv(spec["password_env"], "").strip()
            entry = {
                "key": spec["key"],
                "role": spec["role"],
                "email_configured": bool(email),
                "password_configured": bool(password),
                "action": "skip",
            }
            if not email:
                entry["reason"] = f"Missing {spec['email_env']}"
                results.append(entry)
                continue

            existing = User.query.filter_by(email=email).first()
            if existing:
                entry["action"] = "exists"
                entry["user_id"] = existing.id
                results.append(entry)
                continue

            if args.dry_run:
                entry["action"] = "would_create"
                results.append(entry)
                continue

            if not password:
                entry["reason"] = f"Missing {spec['password_env']} for new account"
                results.append(entry)
                continue

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
        "mode": "dry-run" if args.dry_run else "apply",
        "accounts": results,
        "idempotent": True,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
