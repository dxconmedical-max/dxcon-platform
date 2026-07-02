import os
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


class SignedUrlTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.extensions.db import db
        from app.storage.factory import init_storage_platform

        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app()
        self.app.config.update({"TESTING": True, "STORAGE_PATH": self.tmp.name, "STORAGE_PROVIDER": "local"})
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        init_storage_platform(self.app)

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        self.tmp.cleanup()

    def test_signed_url_download(self):
        upload = self.client.post(
            "/api/v1/files/upload",
            data={"file": (BytesIO(b"signed"), "report.pdf")},
            content_type="multipart/form-data",
        )
        file_id = upload.get_json()["id"]
        signed = self.client.post(f"/api/v1/files/{file_id}/signed-url")
        url = signed.get_json()["signed_url"]["url"]
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        download = self.client.get(f"{parsed.path}?token={query['token'][0]}&expires={query['expires'][0]}")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.data, b"signed")


if __name__ == "__main__":
    unittest.main()
