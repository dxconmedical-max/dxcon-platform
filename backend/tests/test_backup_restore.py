import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.backup_restore_lib import (
    build_manifest,
    create_sample_backups,
    run_backup_restore_verification,
    verify_manifest,
    verify_postgres_backup,
    verify_uploads_backup,
)


class BackupRestoreTestCase(unittest.TestCase):
    def test_sample_postgres_backup_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = create_sample_backups(Path(tmp))
            report = verify_postgres_backup(artifacts["postgres"])
            self.assertTrue(report["ok"], report)

    def test_sample_uploads_backup_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            artifacts = create_sample_backups(Path(tmp))
            report = verify_uploads_backup(artifacts["uploads"])
            self.assertTrue(report["ok"], report)

    def test_manifest_checksum_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            artifacts = create_sample_backups(base)
            build_manifest(base, artifacts)
            report = verify_manifest(base / "backup-manifest.json", base)
            self.assertTrue(report["ok"], report)
            self.assertEqual(report["artifact_count"], 2)

    def test_manifest_detects_checksum_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            artifacts = create_sample_backups(base)
            build_manifest(base, artifacts)
            with artifacts["postgres"].open("ab") as handle:
                handle.write(b"tamper")
            report = verify_manifest(base / "backup-manifest.json", base)
            self.assertFalse(report["ok"])

    def test_full_backup_restore_verification(self):
        result = run_backup_restore_verification()
        self.assertTrue(result["ok"], result)


if __name__ == "__main__":
    unittest.main()
