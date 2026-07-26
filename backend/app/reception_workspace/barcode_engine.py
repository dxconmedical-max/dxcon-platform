"""Reception Barcode Engine — labels for order, sample, collection.

Reuses ``generate_barcodes`` for stable identifiers. Adds label rendering,
thermal sheets, and printer abstraction (no hardware drivers).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.reception_workspace.audit import write_reception_audit
from app.reception_workspace.errors import ReceptionWorkspaceError
from app.reception_workspace.printers import get_printer, list_printers

LABEL_ORDER = "order"
LABEL_SAMPLE = "sample"
LABEL_COLLECTION = "collection"
LABEL_PATIENT = "patient"

LABEL_TYPES = (LABEL_ORDER, LABEL_SAMPLE, LABEL_COLLECTION, LABEL_PATIENT)


def _esc(value: Any) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _load_barcode_payload(order_ref: str) -> dict[str, Any]:
    from app.reception_workspace.service import generate_barcodes

    return generate_barcodes(order_ref)


def build_labels(order_ref: str, *, types: list[str] | None = None) -> dict[str, Any]:
    payload = _load_barcode_payload(order_ref)
    wanted = {t.strip().lower() for t in (types or list(LABEL_TYPES)) if t}
    if not wanted:
        wanted = set(LABEL_TYPES)

    labels: list[dict[str, Any]] = []

    if LABEL_ORDER in wanted and payload.get("order_barcode"):
        labels.append(
            {
                "type": LABEL_ORDER,
                "title": "Order",
                "code": payload["order_barcode"],
                "subtitle": payload.get("order_code"),
                "lines": [
                    f"Order {payload.get('order_code')}",
                    f"Patient {payload.get('patient_name')} ({payload.get('patient_code')})",
                ],
            }
        )

    if LABEL_PATIENT in wanted and payload.get("patient_barcode"):
        labels.append(
            {
                "type": LABEL_PATIENT,
                "title": "Patient",
                "code": payload["patient_barcode"],
                "subtitle": payload.get("patient_code"),
                "lines": [
                    f"{payload.get('patient_name')}",
                    f"Code {payload.get('patient_code')}",
                ],
            }
        )

    if LABEL_SAMPLE in wanted:
        for sample in payload.get("sample_barcodes") or []:
            labels.append(
                {
                    "type": LABEL_SAMPLE,
                    "title": "Sample",
                    "code": sample.get("barcode"),
                    "subtitle": sample.get("specimen_code"),
                    "lines": [
                        f"{sample.get('test_name')} ({sample.get('test_code')})",
                        f"Specimen {sample.get('specimen_code')}",
                        f"Type {sample.get('sample_type') or '—'}",
                    ],
                    "sample": sample,
                }
            )

    if LABEL_COLLECTION in wanted:
        collection_code = payload.get("collection_barcode")
        if collection_code:
            labels.append(
                {
                    "type": LABEL_COLLECTION,
                    "title": "Collection",
                    "code": collection_code,
                    "subtitle": payload.get("order_code"),
                    "lines": [
                        f"Collection {collection_code}",
                        f"Order {payload.get('order_code')}",
                    ],
                }
            )
        else:
            # Explicit empty collection label slot for UI messaging
            labels.append(
                {
                    "type": LABEL_COLLECTION,
                    "title": "Collection",
                    "code": None,
                    "subtitle": "Not assigned",
                    "lines": [
                        "Collection barcode not available",
                        "Create collection / handoff first",
                    ],
                    "unavailable": True,
                }
            )

    return {
        "order_code": payload.get("order_code"),
        "patient_code": payload.get("patient_code"),
        "patient_name": payload.get("patient_name"),
        "generated_at": payload.get("generated_at") or datetime.utcnow().isoformat() + "Z",
        "reprint": bool(payload.get("reprint")),
        "barcodes": payload,
        "labels": labels,
        "printers": list_printers(),
    }


def render_label_html(labels: list[dict[str, Any]], *, thermal: bool = False) -> str:
    width = "80mm" if thermal else "50mm"
    height = "40mm" if thermal else "30mm"
    cards = []
    for label in labels:
        if label.get("unavailable") and not label.get("code"):
            body = "<div class='muted'>Unavailable</div>"
        else:
            lines = "".join(f"<div>{_esc(line)}</div>" for line in (label.get("lines") or []))
            body = (
                f"<div class='title'>{_esc(label.get('title'))}</div>"
                f"<div class='code'>{_esc(label.get('code'))}</div>"
                f"{lines}"
            )
        cards.append(f"<div class='label'>{body}</div>")
    return f"""<!doctype html>
<html><head><meta charset="utf-8"/><title>DxCon Labels</title>
<style>
@page {{ size: {width} {height}; margin: 2mm; }}
body {{ font-family: ui-monospace, Menlo, monospace; margin: 0; }}
.label {{ width: {width}; min-height: {height}; border: 1px dashed #94a3b8; padding: 3mm; box-sizing: border-box; page-break-after: always; }}
.title {{ font-weight: 700; font-size: 11px; text-transform: uppercase; }}
.code {{ font-size: 14px; font-weight: 700; letter-spacing: .04em; margin: 4px 0; word-break: break-all; }}
.muted {{ color: #64748b; font-size: 11px; }}
div {{ font-size: 10px; margin: 1px 0; }}
</style></head><body>
{''.join(cards)}
</body></html>"""


def render_thermal_text(labels: list[dict[str, Any]]) -> str:
    blocks: list[str] = []
    for label in labels:
        blocks.append(label.get("title") or "LABEL")
        blocks.append("-" * 24)
        if label.get("code"):
            blocks.append(str(label["code"]))
        for line in label.get("lines") or []:
            blocks.append(str(line))
        blocks.append("")
    return "\n".join(blocks).rstrip() + "\n"


def preview_labels(
    order_ref: str,
    *,
    types: list[str] | None = None,
    format: str = "standard",
) -> dict[str, Any]:
    bundle = build_labels(order_ref, types=types)
    printable = [lab for lab in bundle["labels"] if lab.get("code")]
    thermal = format == "thermal"
    return {
        **bundle,
        "format": "thermal" if thermal else "standard",
        "html": render_label_html(printable or bundle["labels"], thermal=thermal),
        "thermal_text": render_thermal_text(printable or bundle["labels"]),
        "printable_count": len(printable),
    }


def print_labels(
    order_ref: str,
    *,
    types: list[str] | None = None,
    format: str = "standard",
    printer: str = "browser",
    actor: str | None = None,
) -> dict[str, Any]:
    bundle = build_labels(order_ref, types=types)
    printable = [lab for lab in bundle["labels"] if lab.get("code")]
    if not printable:
        raise ReceptionWorkspaceError("No printable barcodes available for selected types")

    thermal = format == "thermal" or printer == "thermal"
    html = render_label_html(printable, thermal=thermal)
    thermal_text = render_thermal_text(printable)
    try:
        adapter = get_printer("thermal" if thermal else printer)
    except ValueError as exc:
        raise ReceptionWorkspaceError(str(exc)) from exc

    job = adapter.create_job(
        title=f"Labels {bundle.get('order_code')}",
        labels=printable,
        html=html,
        thermal_text=thermal_text,
        meta={
            "order_code": bundle.get("order_code"),
            "format": "thermal" if thermal else "standard",
            "types": sorted({lab["type"] for lab in printable}),
        },
    )
    write_reception_audit(
        action="barcode_labels_printed",
        object_type="order",
        object_id=str(bundle.get("order_code") or order_ref),
        actor=actor,
    )
    return {
        "order_code": bundle.get("order_code"),
        "job": job.to_dict(),
        "labels": printable,
        "format": "thermal" if thermal else "standard",
        "printers": list_printers(),
    }


def get_barcode_bundle(order_ref: str) -> dict[str, Any]:
    """Full barcode payload + structured labels for the Barcode page."""
    return build_labels(order_ref)
