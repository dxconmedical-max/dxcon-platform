import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class RepositoryHygieneTestCase(unittest.TestCase):
    def test_env_not_tracked(self):
        proc = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "backend/.env"],
            cwd=str(REPO),
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_gitignore_covers_hygiene_paths(self):
        gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")
        for pattern in (
            ".env",
            "*.pyc",
            "__pycache__/",
            "__MACOSX/",
            ".DS_Store",
            ".pytest_cache/",
            ".mypy_cache/",
            ".ruff_cache/",
            "generated_reports/",
            "instance/",
            "uploads/tmp/",
            "*.save",
        ):
            self.assertIn(pattern, gitignore)

    def test_env_safety_verification(self):
        from scripts.env_safety_lib import run_env_safety_verification

        result = run_env_safety_verification()
        self.assertTrue(result["ok"], result)


if __name__ == "__main__":
    unittest.main()
