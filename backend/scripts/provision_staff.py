"""Provision DxCon staff accounts from a CSV kept OUTSIDE the repo.

Dry run by default; --apply writes. Passwords are random, printed once, never stored.
Never creates admin-level or external roles; never changes an existing user's role or password.
Columns: full_name, email, role   (users have no name column; full_name is only echoed back)
"""

from __future__ import annotations

import argparse
import csv
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# platform role -> role inside the internal organization
STAFF_ROLES = {
    "ADMIN": "CLINIC_ADMIN",
    "RECEPTION": "RECEPTION",
    "COLLECTOR": "COLLECTOR",
    "LAB": "LAB",
    "DOCTOR": "DOCTOR",
    "ACCOUNTING": "FINANCE",
}
REQUIRED = {"full_name", "email", "role"}


def read_rows(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows or not REQUIRED.issubset(rows[0].keys()):
        raise SystemExit(f"{path}: needs columns {sorted(REQUIRED)}")
    return rows


def _validate(rows: list[dict]) -> list[tuple[str, str, str]]:
    seen, out = set(), []
    for row in rows:
        name = (row.get("full_name") or "").strip()
        email = (row.get("email") or "").strip().lower()
        role = (row.get("role") or "").strip().upper()
        if not name or "@" not in email:
            raise SystemExit(f"bad row: {row}")
        if role not in STAFF_ROLES:
            raise SystemExit(f"{email}: role '{role}' is not allowed (allowed: {sorted(STAFF_ROLES)})")
        if email in seen:
            raise SystemExit(f"{email}: listed twice")
        seen.add(email)
        out.append((name, email, role))
    return out


def provision(rows: list[dict], apply: bool) -> list[dict]:
    from app.core.passwords import hash_password
    from app.extensions.db import db
    from app.models.partner_foundation import OrganizationUser, PartnerOrganization
    from app.models.user import User

    staff = _validate(rows)
    internal = PartnerOrganization.query.filter_by(organization_type="DXCON_INTERNAL").first()
    if internal is None:
        raise SystemExit("internal organization (DXCON_INTERNAL) not found; refusing")
    for _, email, role in staff:
        user = User.query.filter_by(email=email).first()
        if user is not None and user.role != role:
            raise SystemExit(f"{email} already exists with role {user.role}; refusing to change it")
        if user is not None and user.organization_id not in (None, internal.id):
            raise SystemExit(f"{email} already belongs to another organization; refusing")

    if apply:
        from app.partner_foundation.service import seed_organization_roles

        seed_organization_roles()

    report = []
    for name, email, role in staff:
        item = {"name": name, "email": email, "role": role, "password": None,
                "user": "create", "membership": "create"}
        user = User.query.filter_by(email=email).first()
        if user is not None:
            item["user"] = "exists"
            if apply and user.organization_id is None:
                user.organization_id = internal.id
        elif apply:
            password = secrets.token_urlsafe(12)
            user = User(email=email, role=role, password_hash=hash_password(password),
                        is_active=True, organization_id=internal.id)
            db.session.add(user)
            db.session.flush()
            item["password"] = password
        if apply and user is not None:
            member = OrganizationUser.query.filter_by(organization_id=internal.id, user_id=user.id).first()
            if member is None:
                db.session.add(OrganizationUser(organization_id=internal.id, user_id=user.id,
                                                role_code=STAFF_ROLES[role], active=True,
                                                invited_by="provision_staff"))
            else:
                item["membership"] = "exists"
        report.append(item)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staff", required=True, help="CSV file (kept outside the repository)")
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = parser.parse_args()
    rows = read_rows(args.staff)

    from app import create_app
    from app.extensions.db import db

    with create_app().app_context():
        report = provision(rows, args.apply)
        if args.apply:
            db.session.commit()

    print("MODE:", "APPLY" if args.apply else "DRY RUN (nothing written)")
    for r in report:
        print(f"{r['role']}: user={r['user']} membership={r['membership']} {r['email']} ({r['name']})")
        if r["password"]:
            print(f"    PASSWORD (shown once): {r['password']}")
    if args.apply:
        print("Done. Copy the passwords now; they are not stored anywhere.")


if __name__ == "__main__":
    main()
