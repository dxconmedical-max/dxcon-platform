import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class SdkGeneratorTestCase(unittest.TestCase):
    def test_generate_sdk_script(self):
        from scripts.artifact_paths import generated_api_dir

        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_sdk.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env={**os.environ},
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        sdk_root = generated_api_dir() / "sdk"
        python_client = sdk_root / "python" / "dxcon_client.py"
        ts_client = sdk_root / "typescript" / "dxcon_client.ts"
        manifest = sdk_root / "manifest.json"
        self.assertTrue(python_client.exists(), python_client)
        self.assertTrue(ts_client.exists(), ts_client)
        self.assertTrue(manifest.exists(), manifest)
        self.assertIn("class DxConClient", python_client.read_text(encoding="utf-8"))
        self.assertIn("export class DxConClient", ts_client.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
