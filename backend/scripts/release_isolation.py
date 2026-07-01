#!/usr/bin/env python3
"""Detect and split mixed release changes before commit."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"

SHARED_WIRING = {
    "backend/app/__init__.py",
    "backend/app/core/statuses.py",
    "backend/app/models/__init__.py",
}

GENERATED_ARTIFACT_PREFIXES = (
    "backend/generated_reports/",
)

INFRASTRUCTURE_PATHS = {
    "backend/scripts/release_isolation.py",
    ".cursor/rules/release-isolation.mdc",
    ".gitignore",
}


@dataclass(frozen=True)
class ReleaseSpec:
    release_id: str
    name: str
    patterns: tuple[str, ...]


RELEASES: tuple[ReleaseSpec, ...] = (
    ReleaseSpec("go-live-day1", "Go-Live Sprint Day 1 - Core Stabilization", (
        "backend/app/core/api_response.py",
        "backend/app/core/list_params.py",
        "backend/app/core/startup_checks.py",
        "backend/app/core/errors.py",
        "backend/app/core/request_context.py",
        "backend/app/core/config.py",
        "backend/app/core/config_validation.py",
        "backend/app/core/deployment.py",
        "backend/app/core/observability.py",
        "backend/app/core/validation.py",
        "backend/app/api/system/routes.py",
        "backend/scripts/generate_api_inventory.py",
        "backend/scripts/go_live_day1_verify.py",
        "backend/scripts/verify_observability.py",
        "backend/scripts/verify_deployment.py",
        "backend/tests/test_go_live_day1.py",
        "backend/tests/test_observability.py",
        "backend/inventory/",
    )),
    ReleaseSpec("4.3", "Healthcare Standards Gateway", (
        "backend/app/standards/",
        "backend/app/models/healthcare_standards.py",
        "backend/app/services/healthcare_standards_service.py",
        "backend/app/api/standards/",
        "backend/app/web/healthcare_standards.py",
        "backend/scripts/seed_standards_demo.py",
        "backend/scripts/verify_standards_gateway.py",
        "backend/scripts/smoke_test_standards_gateway.py",
        "backend/tests/standards_test_helpers.py",
        "backend/tests/test_standards_core.py",
        "backend/tests/test_hl7_foundation.py",
        "backend/tests/test_fhir_foundation.py",
        "backend/tests/test_code_mapping.py",
        "backend/tests/test_dicom_metadata.py",
    )),
    ReleaseSpec("4.2", "API Platform & OpenAPI SDK", (
        "backend/app/api_platform/",
        "backend/app/models/api_platform.py",
        "backend/app/services/api_platform_service.py",
        "backend/app/api/api_platform/",
        "backend/app/web/api_platform.py",
        "backend/scripts/generate_sdk.py",
        "backend/scripts/verify_api_platform.py",
        "backend/scripts/smoke_test_api_platform.py",
        "backend/tests/test_api_platform.py",
        "backend/tests/test_openapi_generator.py",
        "backend/tests/test_api_keys.py",
        "backend/tests/test_sdk_generator.py",
        "backend/generated_api/",
        "backend/static/openapi/",
    )),
    ReleaseSpec("4.1", "Integration Platform Core", (
        "backend/app/integrations/",
        "backend/app/plugins/",
        "backend/app/events/",
        "backend/app/models/integration_platform.py",
        "backend/app/services/integration_platform_service.py",
        "backend/app/api/integration_platform/",
        "backend/app/web/integration_platform.py",
        "backend/scripts/verify_integration_platform.py",
        "backend/scripts/smoke_test_integration_platform.py",
        "backend/tests/test_adapter_framework.py",
        "backend/tests/test_plugin_framework.py",
        "backend/tests/test_event_bus.py",
        "backend/tests/test_webhooks.py",
        "backend/tests/test_integration_queue.py",
        "backend/tests/test_integration_sandbox.py",
        "backend/app/api/communication/routes.py",
        "backend/scripts/verify_notifications.py",
        "backend/scripts/smoke_test_notifications.py",
        "backend/tests/test_communication_hub.py",
    )),
    ReleaseSpec("4.0", "Enterprise Platform", (
        "backend/app/models/enterprise_platform.py",
        "backend/app/services/enterprise_platform_service.py",
        "backend/app/api/enterprise/",
        "backend/app/web/enterprise_platform.py",
        "backend/scripts/verify_enterprise.py",
        "backend/scripts/smoke_test_enterprise.py",
        "backend/tests/test_enterprise_platform.py",
    )),
    ReleaseSpec("3.9", "Communication & Automation Hub", (
        "backend/app/models/communication_hub.py",
        "backend/app/services/communication_hub_service.py",
        "backend/app/api/communication/",
        "backend/app/web/communication_hub.py",
        "backend/scripts/verify_notifications.py",
        "backend/scripts/smoke_test_notifications.py",
        "backend/tests/test_communication_hub.py",
    )),
    ReleaseSpec("3.8", "Medical Knowledge & Guideline Engine", (
        "backend/app/models/knowledge_engine.py",
        "backend/app/services/knowledge_engine_service.py",
        "backend/app/api/knowledge/",
        "backend/app/web/knowledge_engine.py",
        "backend/scripts/verify_knowledge.py",
        "backend/scripts/smoke_test_knowledge.py",
        "backend/tests/test_knowledge.py",
    )),
    ReleaseSpec("3.7", "AI Clinical Decision Support", (
        "backend/app/models/ai_cds.py",
        "backend/app/services/ai_cds_service.py",
        "backend/app/api/ai_cds/",
        "backend/app/web/ai_cds.py",
        "backend/scripts/verify_ai.py",
        "backend/scripts/smoke_test_ai.py",
        "backend/tests/test_ai_rules.py",
        "backend/tests/test_ai_interpretation.py",
        "backend/tests/test_ai_risk.py",
    )),
    ReleaseSpec("3.6", "Multi-Lab Federation Platform", (
        "backend/app/models/federation_",
        "backend/app/services/federation_",
        "backend/app/api/federation/",
        "backend/app/web/federation.py",
        "backend/scripts/seed_federation_demo.py",
        "backend/scripts/verify_federation.py",
        "backend/scripts/smoke_test_federation.py",
        "backend/tests/test_federation",
    )),
    ReleaseSpec("3.5", "Reporting & Business Intelligence", (
        "backend/app/models/reporting_platform.py",
        "backend/app/services/kpi_engine_service.py",
        "backend/app/services/analytics_engine_service.py",
        "backend/app/services/dashboard_platform_service.py",
        "backend/app/services/report_platform_service.py",
        "backend/scripts/verify_dashboard.py",
        "backend/scripts/verify_kpi.py",
        "backend/scripts/verify_analytics.py",
        "backend/tests/test_dashboard.py",
        "backend/tests/test_kpi.py",
        "backend/tests/test_analytics.py",
        "backend/tests/test_scheduled_reports.py",
    )),
    ReleaseSpec("3.3", "Logistics 2.0", (
        "backend/app/models/logistics_",
        "backend/app/services/logistics_platform_service.py",
        "backend/app/api/logistics/",
        "backend/app/web/logistics_v2.py",
        "backend/scripts/verify_logistics",
    )),
    ReleaseSpec("3.2", "Laboratory Operations Platform", (
        "backend/app/models/lab_facility.py",
        "backend/app/models/lab_accession.py",
        "backend/app/models/lab_operations.py",
        "backend/app/services/lab_workflow_service.py",
        "backend/app/services/lab_dashboard_service.py",
        "backend/app/api/lab/",
        "backend/scripts/verify_lab_operations.py",
    )),
    ReleaseSpec("3.1", "CRM & Sales Platform", (
        "backend/app/models/crm_",
        "backend/app/services/crm_",
        "backend/app/api/crm/",
        "backend/scripts/verify_crm.py",
        "backend/tests/test_crm.py",
        "backend/tests/test_sales.py",
        "backend/tests/test_contracts.py",
    )),
    ReleaseSpec("1.0", "Result Gateway MVP", (
        "backend/app/models/lab_result",
        "backend/app/models/result_attachment.py",
        "backend/app/models/result_review.py",
        "backend/app/models/result_release.py",
        "backend/app/models/result_timeline.py",
        "backend/app/services/result_gateway_service.py",
        "backend/app/api/results/",
        "backend/app/web/result_gateway.py",
        "backend/scripts/verify_results.py",
        "backend/tests/test_results.py",
    )),
)


def _normalize(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def changed_files(include_untracked: bool = True) -> list[str]:
    files = set(_git_lines("diff", "--name-only"))
    files.update(_git_lines("diff", "--cached", "--name-only"))
    if include_untracked:
        files.update(_git_lines("ls-files", "--others", "--exclude-standard"))
    return sorted(
        path
        for path in (_normalize(item) for item in files)
        if (
            (path.startswith("backend/") or path in INFRASTRUCTURE_PATHS)
            and not _is_artifact(path)
        )
    )


def _is_artifact(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in GENERATED_ARTIFACT_PREFIXES)


def classify_file(path: str) -> str:
    normalized = _normalize(path)
    if normalized in SHARED_WIRING:
        return "shared"
    if normalized in INFRASTRUCTURE_PATHS:
        return "infrastructure"
    for spec in RELEASES:
        for pattern in spec.patterns:
            if normalized.startswith(pattern) or pattern in normalized:
                return spec.release_id
    return "unknown"


def group_files(files: list[str]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for path in files:
        grouped[classify_file(path)].append(path)
    return dict(grouped)


def exclusive_releases(grouped: dict[str, list[str]]) -> dict[str, list[str]]:
    return {
        release_id: paths
        for release_id, paths in grouped.items()
        if release_id not in {"shared", "unknown", "infrastructure"} and paths
    }


def check_isolation(target_release: str | None = None) -> int:
    files = changed_files()
    if not files:
        print("OK: no pending backend changes")
        return 0

    grouped = group_files(files)
    exclusive = exclusive_releases(grouped)
    release_ids = sorted(exclusive.keys())

    print("Changed files by release:")
    for release_id in ["shared", "infrastructure", *[r.release_id for r in RELEASES], "unknown"]:
        paths = grouped.get(release_id, [])
        if not paths:
            continue
        label = release_id
        if release_id not in {"shared", "unknown", "infrastructure"}:
            name = next(r.name for r in RELEASES if r.release_id == release_id)
            label = f"{release_id} ({name})"
        print(f"\n[{label}]")
        for path in paths:
            print(" ", path)

    if len(release_ids) > 1:
        print("\nCONFLICT: multiple exclusive releases in working tree:")
        for release_id in release_ids:
            print(f"  - {release_id}: {len(exclusive[release_id])} file(s)")
        print("\nSplit required before commit. Run:")
        print("  python backend/scripts/release_isolation.py split-plan")
        return 1

    if target_release and release_ids and release_ids[0] != target_release:
        print(f"\nCONFLICT: changes belong to release {release_ids[0]}, not {target_release}")
        return 1

    if grouped.get("unknown"):
        print("\nWARN: unclassified files (review before commit):")
        for path in grouped["unknown"]:
            print(" ", path)
        return 1

    active = release_ids[0] if release_ids else "shared-or-infrastructure"
    print(f"\nOK: isolated for release {active}")
    return 0


def split_plan() -> int:
    files = changed_files()
    grouped = group_files(files)
    exclusive = exclusive_releases(grouped)
    shared = grouped.get("shared", [])

    if len(exclusive) <= 1 and not grouped.get("unknown"):
        print("OK: no split needed")
        return 0

    print("Suggested isolated commits:\n")
    for spec in RELEASES:
        paths = exclusive.get(spec.release_id, [])
        if not paths:
            continue
        commit_files = paths + shared
        print(f"Release {spec.release_id} - {spec.name}")
        print(f'git add {" ".join(commit_files)}')
        print(
            "git commit -m \"Release "
            f"{spec.release_id} - {spec.name}\"\n"
        )

    if grouped.get("unknown"):
        print("Unclassified (manual review):")
        for path in grouped["unknown"]:
            print(" ", path)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Release isolation checker")
    parser.add_argument(
        "command",
        choices=("check", "split-plan"),
        help="check working tree or print split plan",
    )
    parser.add_argument("--release", help="expected release id, e.g. 3.6")
    args = parser.parse_args()

    if args.command == "check":
        return check_isolation(args.release)
    return split_plan()


if __name__ == "__main__":
    sys.exit(main())
