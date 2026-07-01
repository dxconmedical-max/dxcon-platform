import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class SdkGeneratorTestCase(unittest.TestCase):
    def test_generate_sdk_script(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_sdk.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        python_client = ROOT / "generated_api" / "sdk" / "python" / "dxcon_client.py"
        ts_client = ROOT / "generated_api" / "sdk" / "typescript" / "dxcon_client.ts"
        manifest = ROOT / "generated_api" / "sdk" / "manifest.json"
        self.assertTrue(python_client.exists())
        self.assertTrue(ts_client.exists())
        self.assertTrue(manifest.exists())
        self.assertIn("class DxConClient", python_client.read_text(encoding="utf-8"))
        self.assertIn("export class DxConClient", ts_client.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
