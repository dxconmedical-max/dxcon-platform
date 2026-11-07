"""Provision clinic organizations and read-only accounts from a CSV kept OUTSIDE the repo.

Dry run by default; --apply writes. Passwords are random, printed once and never stored.
Never changes an existing user's role or password.
Columns: organization_code, organization_name, viewer_email [, contact_name, contact_email]
"""

from __future__ import annotations

import argparse
import csv
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CLINIC_ROLE = "CLINIC_VIEWER"
REQUIRED = {"organization_code", "organization_name", "viewer_email"}


def read_rows(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows or not REQUIRED.issubset(rows[0].keys()):
        raise SystemExit(f"{path}: needs columns {sorted(REQUIRED)}")
    return rows


def provision(rows: list[dict], apply: bool) -> list[dict]:
    from app.core.passwords import hash_password
    from app.extensions.db import db
    from app.models.partner_foundation import OrganizationUser, PartnerOrganization
    from app.models.user import User

    if apply:
        from app.partner_foundation.service import seed_organization_roles

        seed_organization_roles()

    report = []
    for row in rows:
        code = (row.get("organization_code") or "").strip().upper()
        name = (row.get("organization_name") or "").strip()
        email = (row.get("viewer_email") or "").strip().lower()
        if not code or not name or "@" not in email:
            raise SystemExit(f"bad row: {row}")

        org = PartnerOrganization.query.filter_by(organization_code=code).first()
        item = {"organization_code": code, "email": email, "password": None,
                "org": "exists" if org else "create", "user": "create", "membership": "create"}
        if org is None and apply:
            org = PartnerOrganization(
                organization_code=code, organization_name=name, organization_type="CLINIC",
                email=(row.get("contact_email") or "").strip() or None,
                contact_person=(row.get("contact_name") or "").strip() or None,
            )
            db.session.add(org)
            db.session.flush()

        user = User.query.filter_by(email=email).first()
        if user is not None:
            if user.role != CLINIC_ROLE:
                raise SystemExit(f"{email} already exists with role {user.role}; refusing to change it")
            if org is not None and user.organization_id not in (None, org.id):
                raise SystemExit(f"{email} already belongs to another organization; refusing")
            item["user"] = "exists"
        elif apply:
            password = secrets.token_urlsafe(12)
            user = User(email=email, role=CLINIC_ROLE, password_hash=hash_password(password),
                        is_active=True, organization_id=org.id)
            db.session.add(user)
            db.session.flush()
            item["password"] = password

        if apply and user is not None and org is not None:
            member = OrganizationUser.query.filter_by(organization_id=org.id, user_id=user.id).first()
            if member is None:
                db.session.add(OrganizationUser(organization_id=org.id, user_id=user.id, role_code="VIEWER",
                                                active=True, invited_by="provision_clinics"))
            else:
                item["membership"] = "exists"
        report.append(item)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clinics", required=True, help="CSV file (kept outside the repository)")
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = parser.parse_args()
    rows = read_rows(args.clinics)

    from app import create_app
    from app.extensions.db import db

    with create_app().app_context():
        report = provision(rows, args.apply)
        if args.apply:
            db.session.commit()

    print("MODE:", "APPLY" if args.apply else "DRY RUN (nothing written)")
    for r in report:
        print(f"{r['organization_code']}: org={r['org']} user={r['user']} membership={r['membership']} {r['email']}")
        if r["password"]:
            print(f"    PASSWORD (shown once): {r['password']}")
    if args.apply:
        print("Done. Copy the passwords now; they are not stored anywhere.")


if __name__ == "__main__":
    main()
