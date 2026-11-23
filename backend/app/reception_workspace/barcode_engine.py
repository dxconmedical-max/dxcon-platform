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



# --- Code 128 (subset B) encoder -> inline SVG, no external dependency -------
_C128 = [
"212222","222122","222221","121223","121322","131222","122213","122312","132212","221213",
"221312","231212","112232","122132","122231","113222","123122","123221","223211","221132",
"221231","213212","223112","312131","311222","321122","321221","312212","322112","322211",
"212123","212321","232121","111323","131123","131321","112313","132113","132311","211313",
"231113","231311","112133","112331","132131","113123","113321","133121","313121","211331",
"231131","213113","213311","213131","311123","311321","331121","312113","312311","332111",
"314111","221411","431111","111224","111422","121124","121421","141122","141221","112214",
"112412","122114","122411","142112","142211","241211","221114","413111","241112","134111",
"111242","121142","121241","114212","124112","124211","411212","421112","421211","212141",
"214121","412121","111143","111341","131141","114113","114311","411113","411311","113141",
"114131","311141","411131","211412","211214","211232","2331112",
]


def code128_svg(value: str, *, height_mm: float = 12.0, width_mm: float = 46.0) -> str:
    """Code 128-B barcode as SVG, stretched to ``width_mm`` (bars run across the label)."""
    text = "".join(ch for ch in str(value) if 32 <= ord(ch) < 127)
    if not text:
        return ""
    codes = [104] + [ord(ch) - 32 for ch in text]
    checksum = (104 + sum((i + 1) * c for i, c in enumerate(codes[1:]))) % 103
    codes += [checksum, 106]
    pattern = "".join(_C128[c] for c in codes)
    total = sum(int(d) for d in pattern)
    x = 0
    rects = []
    for i, d in enumerate(pattern):
        w = int(d)
        if i % 2 == 0:
            rects.append(f"<rect x='{x}' y='0' width='{w}' height='10'/>")
        x += w
    return (
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {total} 10' "
        f"preserveAspectRatio='none' width='{width_mm}mm' height='{height_mm}mm' "
        f"shape-rendering='crispEdges' fill='#000'>{''.join(rects)}</svg>"
    )


TUBE_SIZES = {"tube50": ("50mm", "25mm", 44.0), "tube45": ("45mm", "25mm", 39.0)}


def render_tube_label_html(labels: list[dict[str, Any]], *, size: str = "tube50") -> str:
    width, height, bar_w = TUBE_SIZES.get(size, TUBE_SIZES["tube50"])
    cards = []
    for label in labels:
        code = label.get("code")
        if not code:
            continue
        sample = label.get("sample") or {}
        lines = label.get("lines") or []
        name_line = _esc(lines[0]) if lines else ""
        type_line = _esc(sample.get("sample_type") or label.get("title") or "")
        cards.append(
            "<div class='label'>"
            f"<div class='bar'>{code128_svg(str(code), height_mm=11.0, width_mm=bar_w)}</div>"
            f"<div class='human'>{_esc(code)}</div>"
            f"<div class='meta'>{name_line}</div>"
            f"<div class='meta'>{type_line}</div>"
            "</div>"
        )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"/><title>DxCon Tube Labels</title>
<style>
@page {{ size: {width} {height}; margin: 0; }}
body {{ font-family: Arial, Helvetica, sans-serif; margin: 0; }}
.label {{ width: {width}; height: {height}; padding: 1.5mm 2.5mm; box-sizing: border-box; overflow: hidden; page-break-after: always; }}
.bar {{ line-height: 0; }}
.human {{ font-size: 8pt; font-weight: 700; text-align: center; letter-spacing: .08em; margin-top: .5mm; }}
.meta {{ font-size: 6.5pt; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
</style></head><body>
{''.join(cards)}
</body></html>"""


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
    tube = format in TUBE_SIZES
    return {
        **bundle,
        "format": format if tube else ("thermal" if thermal else "standard"),
        "html": (
            render_tube_label_html(printable, size=format)
            if tube
            else render_label_html(printable or bundle["labels"], thermal=thermal)
        ),
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

    tube = format in TUBE_SIZES
    thermal = (format == "thermal" or printer == "thermal") and not tube
    html = (
        render_tube_label_html(printable, size=format)
        if tube
        else render_label_html(printable, thermal=thermal)
    )
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
            "format": format if tube else ("thermal" if thermal else "standard"),
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
        "format": format if tube else ("thermal" if thermal else "standard"),
        "printers": list_printers(),
    }


def get_barcode_bundle(order_ref: str) -> dict[str, Any]:
    """Full barcode payload + structured labels for the Barcode page."""
    return build_labels(order_ref)
