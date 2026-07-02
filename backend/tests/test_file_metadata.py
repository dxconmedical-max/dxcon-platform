import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")


class FileMetadataTestCase(unittest.TestCase):
    def setUp(self):
        from app import create_app
        from app.extensions.db import db
        from app.storage.attachment_service import AttachmentService
        from app.storage.factory import init_storage_platform

        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app()
        self.app.config.update({"TESTING": True, "STORAGE_PATH": self.tmp.name, "STORAGE_PROVIDER": "local"})
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        init_storage_platform(self.app)
        self.metadata = AttachmentService.upload_file(
            filename="lab.pdf",
            content_type="application/pdf",
            data=b"%PDF-1.4 test",
            tenant_id="TEN-001",
        )

    def tearDown(self):
        from app.extensions.db import db

        db.session.remove()
        db.drop_all()
        self.ctx.pop()
        self.tmp.cleanup()

    def test_metadata_fields(self):
        required = {
            "id",
            "tenant_id",
            "filename",
            "content_type",
            "size_bytes",
            "storage_provider",
            "storage_key",
            "checksum_sha256",
            "status",
            "virus_scan_status",
            "retention_until",
            "created_at",
            "updated_at",
        }
        self.assertTrue(required.issubset(set(self.metadata)))
        self.assertEqual(self.metadata["tenant_id"], "TEN-001")
        self.assertEqual(self.metadata["status"], "ACTIVE")


if __name__ == "__main__":
    unittest.main()
