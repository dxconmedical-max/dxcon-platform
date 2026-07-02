"""Enterprise Hardening Pack 8 - Code Quality verification."""

from __future__ import annotations

import ast

from scripts.enterprise_hardening_lib import (
    check_bare_except,
    check_bootstrap_layout,
    check_broad_except_pass,
    check_duplicate_helper_names,
)
from scripts.enterprise_master_lib import (
    ROOT,
    run_compileall,
    run_release_isolation,
    run_unit_tests,
    scan_python_files,
    score_from_checks,
    utc_now,
    write_report,
)

RELEASE_ID = "enterprise-hardening-pack-8"


def scan_unused_imports_sample() -> dict:
    findings = []
    for path in list(scan_python_files(ROOT / "app" / "core"))[:20]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = {
            node.names[0].name.split(".")[0]
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom)) and getattr(node, "names", None)
        }
        body = path.read_text(encoding="utf-8")
        unused = [name for name in imports if name not in body.split("\n", 1)[-1]]
        if unused:
            findings.append({"file": str(path.relative_to(ROOT)), "unused": unused[:5]})
    return {"ok": len(findings) <= 5, "sample_findings": findings}


def scan_module_cohesion() -> dict:
    large_files = []
    for path in scan_python_files(ROOT / "app"):
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > 800:
            large_files.append({"file": str(path.relative_to(ROOT)), "lines": lines})
    return {"ok": len(large_files) <= 10, "large_files": large_files[:15]}


def run_code_quality_report() -> dict:
    checks = {
        "no_bare_except": check_bare_except(),
        "no_broad_except_pass": check_broad_except_pass(),
        "duplicate_helpers": check_duplicate_helper_names(),
        "unused_import_sample": scan_unused_imports_sample(),
        "module_cohesion": scan_module_cohesion(),
    }
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": checks,
        "score": score_from_checks(checks),
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("code_quality.json", report)
    return report


def run_architecture_quality_report() -> dict:
    checks = {
        "bootstrap_layout": check_bootstrap_layout(),
        "blueprint_registry": __import__("scripts.blueprint_registry_lib", fromlist=["run_blueprint_registry_verification"]).run_blueprint_registry_verification(),
    }
    report = {
        "generated_at": utc_now(),
        "release": RELEASE_ID,
        "checks": checks,
        "score": score_from_checks(checks),
        "ok": all(item.get("ok") for item in checks.values()),
    }
    write_report("architecture_quality.json", report)
    return report


def run_code_quality_excellence_verification() -> dict:
    compile_result = run_compileall()
    quality = run_code_quality_report()
    architecture = run_architecture_quality_report()
    tests = run_unit_tests()
    sections = {
        "compile": compile_result,
        "code_quality": quality,
        "architecture_quality": architecture,
        "unit_tests": tests,
    }
    ok = all(section.get("ok") for section in sections.values())
    return {"ok": ok, "sections": sections, "score": quality.get("score", 0)}
