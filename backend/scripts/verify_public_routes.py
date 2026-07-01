#!/usr/bin/env python3
"""Verify public route inventory for staging security review."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.security_preflight_lib import inventory_public_routes, run_security_preflight


def main():
    print("\n=== DXCON PUBLIC ROUTE INVENTORY ===\n")
    result = run_security_preflight()
    public = result["checks"]["public_routes"]
    print(f"Public routes: {public['public_count']}")
    print(f"Protected routes: {public['protected_count']}")
    print(f"Internal/unauthenticated routes: {public['internal_count']}")
    for route in public["public_routes"][:15]:
        print(f"  PUBLIC {route['methods']} {route['path']}")
    if len(public["public_routes"]) > 15:
        print(f"  ... and {len(public['public_routes']) - 15} more")
    if not public["ok"]:
        sys.exit(1)
    print("\nPUBLIC ROUTE INVENTORY PASSED\n")


if __name__ == "__main__":
    main()
