# Test package marker so helpers can be imported as tests.p06_auth_helper.
#
# Redirect generated/upload artifact dirs to a writable temp tree. Some local
# agent/CI sandboxes cannot create files under backend/generated_* (EPERM).
# Production paths remain the default when those directories are writable.
from __future__ import annotations

import os
import tempfile
from pathlib import Path

_ARTIFACT_ROOT = Path(tempfile.gettempdir()) / "dxcon_unittest_artifacts"
_ARTIFACT_MAP = {
    "DXCON_GENERATED_RELEASE": "generated_release",
    "DXCON_GENERATED_API": "generated_api",
    "DXCON_GENERATED_REPORTS": "generated_reports",
    "DXCON_UPLOADS_DIR": "uploads",
    "DXCON_DEPLOYMENT_REPORTS": "deployment_reports",
}
for _env_key, _name in _ARTIFACT_MAP.items():
    _path = _ARTIFACT_ROOT / _name
    _path.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault(_env_key, str(_path))
