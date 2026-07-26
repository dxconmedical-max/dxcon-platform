"""Printer abstraction for Reception label output.

Does not talk to hardware drivers directly — adapters produce print jobs
(HTML / thermal text) for the browser or a thermal spooler bridge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class PrintJob:
    """Portable print job returned by printer adapters."""

    job_id: str
    printer: str
    media: str  # label | thermal_label
    title: str
    html: str
    thermal_text: str
    labels: list[dict[str, Any]] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "printer": self.printer,
            "media": self.media,
            "title": self.title,
            "html": self.html,
            "thermal_text": self.thermal_text,
            "labels": self.labels,
            "meta": self.meta,
        }


class PrinterAdapter(Protocol):
    name: str

    def create_job(
        self,
        *,
        title: str,
        labels: list[dict[str, Any]],
        html: str,
        thermal_text: str,
        meta: dict[str, Any] | None = None,
    ) -> PrintJob: ...


class BrowserPrinter:
    """Default browser print dialog (CSS label sheets)."""

    name = "browser"

    def create_job(
        self,
        *,
        title: str,
        labels: list[dict[str, Any]],
        html: str,
        thermal_text: str,
        meta: dict[str, Any] | None = None,
    ) -> PrintJob:
        import uuid

        return PrintJob(
            job_id=f"JOB-{uuid.uuid4().hex[:10].upper()}",
            printer=self.name,
            media="label",
            title=title,
            html=html,
            thermal_text=thermal_text,
            labels=labels,
            meta=meta or {},
        )


class ThermalPrinter:
    """80mm thermal label adapter — HTML + plain-text payload for ESC/POS bridges."""

    name = "thermal"

    def create_job(
        self,
        *,
        title: str,
        labels: list[dict[str, Any]],
        html: str,
        thermal_text: str,
        meta: dict[str, Any] | None = None,
    ) -> PrintJob:
        import uuid

        return PrintJob(
            job_id=f"JOB-{uuid.uuid4().hex[:10].upper()}",
            printer=self.name,
            media="thermal_label",
            title=title,
            html=html,
            thermal_text=thermal_text,
            labels=labels,
            meta={**(meta or {}), "width_mm": 80},
        )


_PRINTERS: dict[str, PrinterAdapter] = {
    BrowserPrinter.name: BrowserPrinter(),
    ThermalPrinter.name: ThermalPrinter(),
}


def list_printers() -> list[dict[str, str]]:
    return [
        {"id": "browser", "name": "Browser print", "media": "label"},
        {"id": "thermal", "name": "Thermal 80mm", "media": "thermal_label"},
    ]


def get_printer(printer_id: str | None) -> PrinterAdapter:
    key = (printer_id or "browser").strip().lower()
    adapter = _PRINTERS.get(key)
    if not adapter:
        raise ValueError(f"Unknown printer: {printer_id}")
    return adapter
