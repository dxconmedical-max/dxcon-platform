"""Environment safety verification helpers."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent

SECRET_PATTERNS = (
    re.compile(r"(?i)(secret|password|token|api_key)\s*=\s*['\"]?[a-zA-Z0-9+/=]{24,}"),
    re.compile(r"(?i)sk-[a-zA-Z0-9]{20,}"),
)

PLACEHOLDER_OK = (
    "change-me",
    "example",
    "your-",
    "replace",
    "localhost",
    "staging.",
    "production.",
    "dxcon",
    "sqlite:",
    "postgresql://",
    "redis://",
)


def git_tracked(path: str) -> bool:
    proc = subprocess.run(
        ["git", "ls-files", "--error-unmatch", path],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def scan_example_secrets(path: Path) -> list[str]:
    if not path.exists():
        return [f"missing file: {path}"]
    findings = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(stripped):
                lowered = stripped.lower()
                if any(token in lowered for token in PLACEHOLDER_OK):
                    continue
                findings.append(f"{path.name}:{line_no}: {stripped}")
    return findings


def run_env_safety_verification() -> dict:
    examples = {
        "env_example": ROOT / ".env.example",
        "staging_example": ROOT / ".env.staging.example",
        "production_example": ROOT / ".env.production.example",
    }
    checks = {
        "env_not_tracked": {"ok": not git_tracked("backend/.env"), "path": "backend/.env"},
        "env_example_exists": {"ok": examples["env_example"].exists()},
        "staging_example_exists": {"ok": examples["staging_example"].exists()},
        "production_example_exists": {"ok": examples["production_example"].exists()},
    }
    secret_findings = []
    for name, path in examples.items():
        secret_findings.extend(scan_example_secrets(path))
    checks["example_secret_scan"] = {"ok": not secret_findings, "findings": secret_findings}
    passed = sum(1 for item in checks.values() if item.get("ok"))
    return {"ok": passed == len(checks), "passed": passed, "total": len(checks), "checks": checks}
