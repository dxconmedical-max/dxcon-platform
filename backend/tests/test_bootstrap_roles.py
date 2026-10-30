import re
import unittest
from pathlib import Path

ROUTES = Path(__file__).resolve().parents[1] / "app" / "api" / "partner_foundation" / "routes.py"


class BootstrapRolesTests(unittest.TestCase):
    def test_bootstrap_is_restricted_to_platform_admins(self):
        src = ROUTES.read_text(encoding="utf-8")
        m = re.search(r'/bootstrap".*?\n@roles_required\(([^)]*)\)\ndef bootstrap', src, re.S)
        self.assertIsNotNone(m, "bootstrap route not found")
        roles = {r.strip().strip('"\'') for r in m.group(1).split(",")}
        self.assertEqual(roles, {"SUPER_ADMIN", "SYSTEM_ADMIN"})


if __name__ == "__main__":
    unittest.main()
