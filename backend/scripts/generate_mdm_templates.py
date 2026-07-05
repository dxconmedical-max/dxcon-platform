#!/usr/bin/env python3
"""Generate CSV and Excel import templates for all MDM entity types."""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TEMPLATES_DIR = ROOT / "templates" / "mdm"
GENERATED = ROOT / "generated_release"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    from app.mdm.registry import ENTITY_TYPES, sample_row, template_columns

    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []

    for entity_type in ENTITY_TYPES:
        cols = template_columns(entity_type)
        sample = sample_row(entity_type)
        csv_path = TEMPLATES_DIR / f"{entity_type}.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            writer.writeheader()
            writer.writerow({c: sample.get(c, "") for c in cols})
        entry = {"entity_type": entity_type, "csv": str(csv_path.relative_to(ROOT)), "columns": cols}
        xlsx_path = TEMPLATES_DIR / f"{entity_type}.xlsx"
        try:
            import openpyxl

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = entity_type[:31]
            ws.append(cols)
            ws.append([sample.get(c, "") for c in cols])
            wb.save(xlsx_path)
            entry["xlsx"] = str(xlsx_path.relative_to(ROOT))
        except ImportError:
            entry["xlsx"] = None
        manifest.append(entry)

    GENERATED.mkdir(parents=True, exist_ok=True)
    (GENERATED / "MDM_TEMPLATES_MANIFEST.json").write_text(json.dumps({
        "generated_at": utc_now(),
        "entity_count": len(ENTITY_TYPES),
        "templates": manifest,
    }, indent=2), encoding="utf-8")

    print(f"Generated {len(manifest)} CSV templates in {TEMPLATES_DIR}")
    xlsx_count = sum(1 for m in manifest if m.get("xlsx"))
    print(f"Excel templates: {xlsx_count} (install openpyxl for all .xlsx)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
