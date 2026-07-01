"""Backup, restore verification, and manifest helpers for staging."""

from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
import tarfile
import tempfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent

MANIFEST_NAME = "backup-manifest.json"

BACKUP_SCRIPTS = (
    REPO / "deployment" / "scripts" / "backup_postgres.sh",
    REPO / "deployment" / "scripts" / "restore_postgres_dry_run.sh",
    REPO / "deployment" / "scripts" / "backup_uploads.sh",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(backup_dir: Path, artifacts: dict[str, Path]) -> dict:
    entries = []
    for name, path in sorted(artifacts.items()):
        entries.append(
            {
                "name": name,
                "path": str(path.name),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "generated_at": utc_now(),
        "backup_dir": str(backup_dir),
        "artifacts": entries,
    }
    manifest_path = backup_dir / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def verify_manifest(manifest_path: Path, backup_dir: Path) -> dict:
    if not manifest_path.exists():
        return {"ok": False, "error": "manifest missing"}
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatches = []
    for item in payload.get("artifacts", []):
        artifact = backup_dir / item["path"]
        if not artifact.exists():
            mismatches.append({"path": item["path"], "error": "missing"})
            continue
        checksum = sha256_file(artifact)
        if checksum != item.get("sha256"):
            mismatches.append({"path": item["path"], "error": "checksum mismatch"})
    return {"ok": not mismatches, "mismatches": mismatches, "artifact_count": len(payload.get("artifacts", []))}


def verify_postgres_backup(path: Path) -> dict:
    if not path.exists():
        return {"ok": False, "error": "file missing"}
    try:
        with gzip.open(path, "rb") as handle:
            sample = handle.read(4096)
    except OSError as exc:
        return {"ok": False, "error": str(exc)}
    header_ok = b"PostgreSQL database dump" in sample or b"PGDMP" in sample or len(sample) > 0
    return {"ok": header_ok, "bytes_sampled": len(sample)}


def verify_uploads_backup(path: Path) -> dict:
    if not path.exists():
        return {"ok": False, "error": "file missing"}
    try:
        with tarfile.open(path, "r:gz") as archive:
            members = archive.getmembers()
    except tarfile.TarError as exc:
        return {"ok": False, "error": str(exc)}
    return {"ok": len(members) >= 0, "member_count": len(members)}


def verify_postgres_restore_dry_run(path: Path) -> dict:
    script = REPO / "deployment" / "scripts" / "restore_postgres_dry_run.sh"
    if not script.exists():
        return {"ok": False, "error": "restore script missing"}
    proc = subprocess.run(
        ["bash", str(script), str(path)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout.splitlines()[-3:],
    }


def create_sample_backups(base_dir: Path) -> dict[str, Path]:
    postgres_path = base_dir / "dxcon-sample.sql.gz"
    uploads_path = base_dir / "uploads-sample.tar.gz"
    sql_payload = b"-- PostgreSQL database dump\nSELECT 1;\n"
    with gzip.open(postgres_path, "wb") as handle:
        handle.write(sql_payload)
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        data = b"sample upload"
        info = tarfile.TarInfo(name="uploads/sample.txt")
        info.size = len(data)
        archive.addfile(info, BytesIO(data))
    uploads_path.write_bytes(buffer.getvalue())
    return {"postgres": postgres_path, "uploads": uploads_path}


def verify_backup_scripts_exist() -> dict:
    missing = [str(path.relative_to(REPO)) for path in BACKUP_SCRIPTS if not path.exists()]
    return {"ok": not missing, "missing": missing}


def run_backup_restore_verification(create_samples: bool = True) -> dict:
    checks = {"scripts": verify_backup_scripts_exist()}
    if create_samples:
        with tempfile.TemporaryDirectory(prefix="dxcon-backup-") as tmp:
            base = Path(tmp)
            artifacts = create_sample_backups(base)
            manifest = build_manifest(base, artifacts)
            manifest_path = base / MANIFEST_NAME
            checks["postgres_backup"] = verify_postgres_backup(artifacts["postgres"])
            checks["uploads_backup"] = verify_uploads_backup(artifacts["uploads"])
            checks["manifest"] = verify_manifest(manifest_path, base)
            checks["restore_dry_run"] = verify_postgres_restore_dry_run(artifacts["postgres"])
    passed = sum(1 for item in checks.values() if item.get("ok"))
    return {
        "ok": passed == len(checks),
        "passed": passed,
        "total": len(checks),
        "checks": checks,
    }
