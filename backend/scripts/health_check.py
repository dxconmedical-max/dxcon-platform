import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import os
import py_compile
from pathlib import Path

print("DXCON HEALTH CHECK START")

files = [
    "run.py",
    "app/__init__.py",
    "app/web/result_upload.py",
    "app/web/patient_portal.py",
    "app/api/system/routes.py",
    "app/api/result_files/routes.py",
]

for f in files:
    if Path(f).exists():
        py_compile.compile(f, doraise=True)
        print("OK compile:", f)
    else:
        print("MISSING:", f)

from app import create_app

app = create_app()

routes = [str(r) for r in app.url_map.iter_rules()]

required = [
    "/",
    "/monitor",
    "/audit",
    "/security",
    "/finance",
    "/executive-v9",
    "/api/v1/system/health",
    "/api/v1/system/stats",
    "/api/v1/system/routes",
    "/api/v1/system/backup-status",
    "/api/v1/result-files",
]

for r in required:
    if r in routes:
        print("OK route:", r)
    else:
        print("MISSING route:", r)

print("TOTAL ROUTES:", len(routes))
print("DXCON HEALTH CHECK DONE")
