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
    "backend/generated_release/",
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
    ReleaseSpec("staging-sprint-4-storage", "Object Storage and File Service", (
        "backend/app/storage/",
        "backend/app/api/files/",
        "backend/app/api/system/routes.py",
        "backend/app/core/config.py",
        "backend/app/models/__init__.py",
        "backend/scripts/storage_stack_lib.py",
        "backend/scripts/verify_storage_stack.py",
        "backend/scripts/storage_smoke_test.py",
        "backend/tests/test_storage_service.py",
        "backend/tests/test_file_metadata.py",
        "backend/tests/test_signed_urls.py",
    )),
    ReleaseSpec("staging-sprint-3-queue-ops", "Background Jobs and Queue Operations", (
        "backend/app/core/queue/",
        "backend/app/core/scheduler/",
        "backend/app/workers/",
        "backend/app/api/system/queue_service.py",
        "backend/app/api/system/routes.py",
        "backend/app/core/config.py",
        "backend/production_start.py",
        "backend/requirements.txt",
        "backend/scripts/queue_stack_lib.py",
        "backend/scripts/verify_queue_stack.py",
        "backend/scripts/verify_worker_health.py",
        "backend/scripts/queue_smoke_test.py",
        "backend/tests/test_queue_runtime.py",
        "backend/tests/test_retry_policy.py",
        "backend/tests/test_worker_runtime.py",
        "backend/tests/test_scheduler.py",
        "backend/tests/test_job_metrics.py",
        "backend/tests/test_production_startup.py",
        "docs/QUEUE_ARCHITECTURE.md",
        "docs/BACKGROUND_JOBS.md",
        "docs/WORKER_GUIDE.md",
    )),
    ReleaseSpec("staging-sprint-2-observability", "Observability and Monitoring", (
        "deployment/monitoring/alerts/",
        "deployment/monitoring/prometheus.yml",
        "deployment/monitoring/grafana/",
        "backend/app/observability/metrics_registry.py",
        "backend/app/observability/metrics_service.py",
        "backend/scripts/monitoring_stack_lib.py",
        "backend/scripts/verify_monitoring_stack.py",
        "backend/scripts/uat_monitoring_smoke.py",
        "backend/tests/test_monitoring_stack.py",
        "backend/tests/test_prometheus_metrics.py",
        "backend/tests/test_log_safety.py",
    )),
    ReleaseSpec("staging-sprint-5", "GA Candidate Validation", (
        "backend/scripts/ga_candidate_lib.py",
        "backend/scripts/verify_ga_candidate.py",
        "backend/scripts/final_ga_smoke.py",
        "backend/generated_release/GA_REPORT.json",
        "backend/generated_release/GA_CHECKLIST.json",
        "backend/generated_release/API_FREEZE_REPORT.json",
    )),
    ReleaseSpec("staging-sprint-4", "Final Security Secrets Review", (
        "backend/scripts/security_preflight_lib.py",
        "backend/scripts/security_preflight.py",
        "backend/scripts/verify_public_routes.py",
        "backend/scripts/verify_admin_security.py",
        "backend/tests/test_security_preflight.py",
        "backend/tests/test_public_route_inventory.py",
    )),
    ReleaseSpec("staging-sprint-3", "UAT Data Tenant Setup", (
        "backend/scripts/uat_tenant_lib.py",
        "backend/scripts/bootstrap_tenant.py",
        "backend/scripts/seed_uat_data.py",
        "backend/scripts/reset_staging_data.py",
        "backend/scripts/verify_uat_data.py",
        "backend/tests/test_tenant_bootstrap.py",
        "backend/tests/test_uat_data.py",
    )),
    ReleaseSpec("staging-sprint-2", "Monitoring Backup Restore", (
        "deployment/monitoring/",
        "deployment/scripts/verify_backup_restore.sh",
        "deployment/scripts/uat_smoke_staging.sh",
        "backend/scripts/backup_restore_lib.py",
        "backend/scripts/staging_monitoring_lib.py",
        "backend/scripts/verify_staging_monitoring.py",
        "backend/scripts/uat_smoke.py",
        "backend/tests/test_backup_restore.py",
        "backend/tests/test_uat_smoke.py",
    )),
    ReleaseSpec("staging-sprint-1", "Production Deployment Stack", (
        "docker-compose.staging.yml",
        "docker-compose.production.yml",
        "deployment/nginx/",
        "deployment/env/",
        "deployment/scripts/bootstrap_staging.sh",
        "deployment/scripts/verify_staging_stack.sh",
        "deployment/scripts/smoke_staging.sh",
        "deployment/scripts/backup_postgres.sh",
        "deployment/scripts/restore_postgres_dry_run.sh",
        "deployment/scripts/backup_uploads.sh",
        "backend/Dockerfile",
        "backend/gunicorn.conf.py",
        "backend/production_start.py",
        "backend/.env.staging.example",
        "backend/.env.production.example",
        "backend/scripts/staging_stack_lib.py",
        "backend/scripts/verify_staging_stack.py",
        "backend/scripts/smoke_test_staging_stack.py",
        "backend/tests/test_staging_stack.py",
        "backend/tests/test_env_validation.py",
        "backend/tests/test_production_startup.py",
    )),
    ReleaseSpec("5.0", "Go-Live RC2 Production Cutover", (
        "backend/scripts/go_live_rc2_lib.py",
        "backend/scripts/final_rc2_smoke.py",
        "backend/scripts/prepare_rollback_package.py",
        "backend/scripts/verify_rollback_package.py",
        "backend/scripts/verify_rc2_cutover.py",
        "backend/scripts/release_isolation.py",
        "backend/tests/test_rc2_cutover.py",
        "backend/tests/test_final_smoke.py",
        "backend/tests/test_rollback_package.py",
    )),
    ReleaseSpec("4.9", "Production Infrastructure & Go-Live Blocker Fix", (
        "backend/app/infrastructure/production_readiness.py",
        "backend/app/infrastructure/runtime_validation.py",
        "backend/app/infrastructure/infrastructure_services.py",
        "backend/app/core/config_validation.py",
        "backend/app/core/security.py",
        "backend/app/observability/health_service.py",
        "backend/.env.production.example",
        "backend/.env.staging.example",
        "backend/scripts/verify_go_live_blockers.py",
        "backend/scripts/smoke_test_production_blockers.py",
        "backend/scripts/check_production_env.py",
        "backend/scripts/verify_postgresql_readiness.py",
        "backend/tests/test_cors_hardening.py",
        "backend/tests/test_redis_readiness.py",
        "backend/tests/test_smtp_readiness.py",
        "backend/tests/test_database_readiness.py",
        "backend/tests/test_observability_health_regression.py",
    )),
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
    ReleaseSpec("4.8", "Go-Live Validation RC1", (
        "backend/scripts/go_live_rc1_lib.py",
        "backend/scripts/e2e_go_live_validation.py",
        "backend/scripts/verify_release_candidate.py",
        "backend/scripts/smoke_test_release_candidate.py",
        "backend/scripts/performance_smoke_test.py",
        "backend/scripts/create_release_tag.py",
        "backend/generated_release/",
        "backend/tests/test_go_live_validation.py",
        "backend/tests/test_release_candidate.py",
        "backend/tests/test_data_integrity.py",
    )),
    ReleaseSpec("4.7", "Deployment & Infrastructure Readiness", (
        "backend/app/runtime/",
        "backend/app/infrastructure/",
        "backend/app/models/infrastructure_readiness.py",
        "backend/app/api/infrastructure/",
        "backend/app/web/deployment_infrastructure.py",
        "backend/Dockerfile",
        "docker-compose.yml",
        "deployment/kubernetes/",
        "deployment/pipeline/",
        "backend/scripts/verify_deployment_readiness.py",
        "backend/scripts/smoke_test_deployment.py",
        "backend/tests/test_runtime_config.py",
        "backend/tests/test_deployment_pipeline.py",
        "backend/tests/test_infrastructure.py",
        "backend/tests/test_scaling.py",
        "backend/tests/test_recovery.py",
    )),
    ReleaseSpec("4.6", "Production Operations Platform", (
        "backend/app/operations/",
        "backend/app/models/operations_platform.py",
        "backend/app/api/operations/",
        "backend/app/web/operations_platform.py",
        "backend/scripts/seed_operations_demo.py",
        "backend/scripts/verify_operations.py",
        "backend/scripts/smoke_test_operations.py",
        "backend/tests/test_operations_scheduler.py",
        "backend/tests/test_operations_backup.py",
        "backend/tests/test_operations_maintenance.py",
        "backend/tests/test_operations_secrets.py",
        "backend/tests/test_operations_deployment.py",
        "backend/tests/test_operations_queues.py",
        "backend/app/web/operations.py",
    )),
    ReleaseSpec("4.5", "Observability Platform", (
        "backend/app/observability/",
        "backend/app/models/observability_platform.py",
        "backend/app/api/observability/",
        "backend/app/web/observability_platform.py",
        "backend/scripts/seed_observability_demo.py",
        "backend/scripts/verify_observability_platform.py",
        "backend/scripts/smoke_test_observability_platform.py",
        "backend/tests/test_metrics.py",
        "backend/tests/test_observability_health.py",
        "backend/tests/test_logging.py",
        "backend/tests/test_alerts.py",
        "backend/tests/test_audit.py",
        "backend/tests/test_tracing.py",
        "backend/app/api/alerts/routes.py",
    )),
    ReleaseSpec("4.4", "Notification & Communication Center", (
        "backend/app/notifications/",
        "backend/app/models/notification_center.py",
        "backend/app/api/notification_center/",
        "backend/app/web/notification_center.py",
        "backend/scripts/seed_notification_center_demo.py",
        "backend/scripts/verify_notification_center.py",
        "backend/scripts/smoke_test_notification_center.py",
        "backend/tests/test_notification_service.py",
        "backend/tests/test_notification_templates.py",
        "backend/tests/test_notification_retry.py",
        "backend/tests/test_notification_providers.py",
        "backend/tests/test_notification_events.py",
        "backend/app/api/notifications/routes.py",
        "backend/app/web/communication_hub.py",
        "backend/tests/test_notifications.py",
        "backend/tests/test_communication_hub.py",
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
