"""Admin test-catalog import: preview, then apply (upsert by code).

The price list itself never lives in the repository. An administrator uploads a CSV
in the web app; the browser parses it and posts rows here. Default is a dry run.
"""

from __future__ import annotations

from functools import wraps

from flask import Blueprint, request, session

from app.api.reception_workspace.routes import _actor, _client_ip
from app.core.audit import write_audit
from app.core.authz import roles_required
from app.extensions.db import db
from app.models.test_catalog import TestCatalog

admin_test_catalog_bp = Blueprint("admin_test_catalog", __name__, url_prefix="/api/v1/admin/test-catalog")

ADMIN_ROLES = frozenset({"SUPER_ADMIN", "ADMIN", "SYSTEM_ADMIN"})
MAX_ROWS = 2000
DEMO_PREFIX = "DEMO-TST-"


def admin_only(fn):
    jwt_wrapped = roles_required(*ADMIN_ROLES)(fn)

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if (session.get("role") or "") in ADMIN_ROLES and session.get("user_id"):
            return fn(*args, **kwargs)
        return jwt_wrapped(*args, **kwargs)

    return wrapper


def _clean_rows(raw) -> tuple[list[dict], list[str]]:
    if not isinstance(raw, list) or not raw:
        return [], ["rows must be a non-empty list"]
    if len(raw) > MAX_ROWS:
        return [], [f"too many rows (max {MAX_ROWS})"]
    errors: list[str] = []
    by_code: dict[str, dict] = {}
    for index, row in enumerate(raw, start=1):
        if not isinstance(row, dict):
            errors.append(f"row {index}: not an object")
            continue
        code = " ".join(str(row.get("code") or "").split())
        name = " ".join(str(row.get("name") or "").split())
        if not code or len(code) > 50:
            errors.append(f"row {index}: code is required (max 50 characters)")
            continue
        if not name or len(name) > 255:
            errors.append(f"row {index} ({code}): name is required (max 255 characters)")
            continue
        try:
            price = float(row.get("price"))
        except (TypeError, ValueError):
            errors.append(f"row {index} ({code}): price must be a number")
            continue
        if price < 0:
            errors.append(f"row {index} ({code}): price cannot be negative")
            continue
        by_code[code] = {
            "code": code,
            "name": name,
            "category": " ".join(str(row.get("category") or "").split())[:100] or None,
            "sample_type": " ".join(str(row.get("sample_type") or "").split())[:100] or None,
            "price": price,
        }
    return list(by_code.values()), errors


@admin_test_catalog_bp.route("/import", methods=["POST"])
@admin_only
def test_catalog_import():
    payload = request.get_json(silent=True) or {}
    rows, errors = _clean_rows(payload.get("rows"))
    if errors:
        return {"success": False, "error": "Invalid rows", "details": errors[:50]}, 400
    apply = payload.get("apply") is True
    remove_demo = payload.get("remove_demo") is True

    existing = {t.code: t for t in TestCatalog.query.all()}
    to_create, to_update, unchanged = [], [], []
    for row in rows:
        current = existing.get(row["code"])
        if current is None:
            to_create.append(row)
        elif (
            current.name != row["name"]
            or (current.category or None) != row["category"]
            or (current.sample_type or None) != row["sample_type"]
            or float(current.price or 0) != row["price"]
        ):
            to_update.append(row)
        else:
            unchanged.append(row)
    incoming = {r["code"] for r in rows}
    demo_codes = sorted(c for c in existing if c.startswith(DEMO_PREFIX) and c not in incoming)

    summary = {
        "create": len(to_create),
        "update": len(to_update),
        "unchanged": len(unchanged),
        "demo_to_remove": len(demo_codes) if remove_demo else 0,
        "demo_present": len(demo_codes),
        "applied": False,
    }
    preview = {"create": to_create[:20], "update": to_update[:20]}
    if not apply:
        return {"success": True, "data": {**summary, "preview": preview}}, 200

    for row in to_create:
        db.session.add(TestCatalog(**row))
    for row in to_update:
        item = existing[row["code"]]
        item.name, item.category, item.sample_type, item.price = (
            row["name"], row["category"], row["sample_type"], row["price"],
        )
    if remove_demo and demo_codes:
        TestCatalog.query.filter(TestCatalog.code.in_(demo_codes)).delete(synchronize_session=False)
    write_audit(
        "TEST_CATALOG_IMPORT", "TestCatalog", f"+{len(to_create)}/~{len(to_update)}/-{summary['demo_to_remove']}",
        user_email=_actor() or "SYSTEM", ip_address=_client_ip(),
    )
    try:
        db.session.commit()
    except Exception:  # noqa: BLE001 - FK from old orders to demo tests, etc.
        db.session.rollback()
        return {
            "success": False,
            "error": "Could not apply (demo tests may still be referenced by old orders). Nothing was changed.",
        }, 409
    summary["applied"] = True
    return {"success": True, "data": summary}, 200
