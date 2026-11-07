"""CLINIC_VIEWER lands on the clinic results page."""

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"


class ClinicViewerWorkspaceTestCase(unittest.TestCase):
    def test_clinic_viewer_workspace(self):
        from app.web_gateway.routing import WORKSPACE_HOME_ROUTES, workspace_path_for_role

        self.assertEqual(workspace_path_for_role("CLINIC_VIEWER"), "/app/clinic-results")
        self.assertEqual(workspace_path_for_role("clinic_viewer"), "/app/clinic-results")
        self.assertIn("/app/clinic-results", WORKSPACE_HOME_ROUTES)

    def test_other_roles_unchanged(self):
        from app.web_gateway.routing import workspace_path_for_role

        self.assertEqual(workspace_path_for_role("CLINIC_ADMIN"), "/app/clinic")
        self.assertEqual(workspace_path_for_role("RECEPTION"), "/app/reception")


if __name__ == "__main__":
    unittest.main()
