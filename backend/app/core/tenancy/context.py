"""Tenant context object attached to Flask `g` — Phase 7.1."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from flask import g


@dataclass
class TenantContext:
    tenant_id: str | None = None
    tenant_code: str | None = None
    tenant_name: str | None = None
    organization_id: str | None = None
    organization_code: str | None = None
    isolation_mode: str | None = None
    schema_name: str | None = None
    resolved: bool = False
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def get_tenant_context() -> TenantContext | None:
    ctx = getattr(g, "tenant_context", None) if g else None
    if isinstance(ctx, TenantContext):
        return ctx
    return None
