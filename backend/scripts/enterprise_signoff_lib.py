"""Enterprise Hardening Pack 10 - Enterprise Sign-off."""

from __future__ import annotations

import json

from scripts.enterprise_master_lib import (
    REPORT_DIR,
    run_compileall,
    run_release_isolation,
    run_unit_tests,
    utc_now,
    write_report,
)

RELEASE_ID = "enterprise-hardening-pack-10"

REQUIRED_REPORTS = {
    "pack_3_database": (
        "database_review.json",
        "database_index_report.json",
        "database_performance_report.json",
    ),
    "pack_4_api": ("api_review.json", "openapi_validation.json", "api_consistency.json"),
    "pack_5_operations": ("operations_review.json", "backup_review.json", "monitoring_review.json"),
    "pack_6_security": ("security_review.json", "security_score.json", "vulnerability_review.json"),
    "pack_7_performance": ("performance_review.json", "latency_review.json", "optimization_report.json"),
    "pack_8_code_quality": ("code_quality.json", "architecture_quality.json"),
    "pack_9_documentation": ("documentation_review.json",),
}


def _load_report(name: str) -> dict:
    path = REPORT_DIR / name
    if not path.exists():
        return {"ok": False, "missing": True}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {"ok": bool(payload.get("ok", True)), "score": payload.get("score"), "payload": payload}


def _score_from_report(report: dict, default: int = 100) -> float:
    if report.get("score") is not None:
        return float(report["score"])
    payload = report.get("payload") or {}
    if "score" in payload:
        return float(payload["score"])
    return float(default) if report.get("ok") else 0.0


def run_enterprise_signoff() -> dict:
    pack_results = {}
    for pack_name, reports in REQUIRED_REPORTS.items():
        checks = {name: _load_report(name) for name in reports}
        pack_results[pack_name] = {
            "ok": all(item.get("ok") for item in checks.values()),
            "checks": checks,
            "score": round(
                sum(_score_from_report(item) for item in checks.values()) / max(len(checks), 1),
                1,
            ),
        }

    compile_result = run_compileall()
    tests = run_unit_tests()
    isolation = run_release_isolation(RELEASE_ID)

    scores = {
        "architecture": pack_results["pack_8_code_quality"]["score"],
        "security": pack_results["pack_6_security"]["score"],
        "performance": pack_results["pack_7_performance"]["score"],
        "production": pack_results["pack_5_operations"]["score"],
    }
    go_live_score = round(sum(scores.values()) / len(scores), 1)

    critical_failures = [name for name, payload in pack_results.items() if not payload.get("ok")]
    if not compile_result.get("ok"):
        critical_failures.append("compile")
    if not tests.get("ok"):
        critical_failures.append("unit_tests")
    if not isolation.get("ok"):
        critical_failures.append("release_isolation")

    if not critical_failures and go_live_score >= 90:
        decision = "READY"
    elif not critical_failures and go_live_score >= 75:
        decision = "READY WITH CONDITIONS"
    else:
        decision = "NOT READY"

    signoff = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "pack_results": {k: {"ok": v.get("ok"), "score": v.get("score")} for k, v in pack_results.items()},
        "compile": compile_result,
        "unit_tests": tests,
        "release_isolation": isolation,
        "ok": decision != "NOT READY",
    }
    write_report("enterprise_signoff.json", signoff)
    write_report("go_live_score.json", {"score": go_live_score, "components": scores, "generated_at": utc_now()})
    write_report("architecture_score.json", {"score": scores["architecture"], "generated_at": utc_now()})
    write_report("security_score.json", {"score": scores["security"], "generated_at": utc_now()})
    write_report("performance_score.json", {"score": scores["performance"], "generated_at": utc_now()})
    write_report("production_score.json", {"score": scores["production"], "generated_at": utc_now()})
    write_report(
        "technical_debt.json",
        {"critical_failures": critical_failures, "go_live_score": go_live_score, "generated_at": utc_now()},
    )
    write_report(
        "go_live_decision.json",
        {
            "decision": decision,
            "go_live_score": go_live_score,
            "critical_failures": critical_failures,
            "generated_at": utc_now(),
        },
    )
    return {
        "ok": signoff["ok"],
        "decision": decision,
        "go_live_score": go_live_score,
        "scores": scores,
        "sections": signoff,
    }
