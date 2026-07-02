import os
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


class StorageServiceTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.extensions.db import db

        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app()
        self.app.config.update(
            {
                "TESTING": True,
                "STORAGE_PATH": self.tmp.name,
                "STORAGE_PROVIDER": "local",
            }
        )
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        from app.storage.factory import init_storage_platform

        init_storage_platform(self.app)

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        self.tmp.cleanup()

    def test_upload_list_and_download(self):
        upload = self.client.post(
            "/api/v1/files/upload",
            data={"file": (BytesIO(b"dxcon"), "sample.pdf")},
            content_type="multipart/form-data",
        )
        self.assertEqual(upload.status_code, 201)
        file_id = upload.get_json()["id"]
        listing = self.client.get("/api/v1/files")
        self.assertEqual(listing.status_code, 200)
        self.assertGreaterEqual(listing.get_json()["count"], 1)
        download = self.client.get(f"/api/v1/files/{file_id}/download")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.data, b"dxcon")

    def test_system_storage_endpoint(self):
        response = self.client.get("/api/v1/system/storage")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("health", payload)
        self.assertIn("metrics", payload)


if __name__ == "__main__":
    unittest.main()
