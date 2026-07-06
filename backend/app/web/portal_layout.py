"""Shared portal layout helpers — Sprint 009."""

from __future__ import annotations

import html


def _h(v: str) -> str:
    return html.escape(str(v))


PORTAL_RESPONSIVE_CSS = """
<style>
.portal-shell { display: grid; gap: 16px; }
@media (min-width: 768px) { .portal-shell { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 1024px) { .portal-shell { grid-template-columns: repeat(3, 1fr); } }
.portal-nav { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
.portal-card { background: var(--launch-card-bg, #fff); border-radius: 12px; padding: 16px; border: 1px solid #e2e8f0; }
@media (prefers-color-scheme: dark) {
  .portal-card { background: #1e293b; border-color: #334155; color: #f1f5f9; }
}
</style>
"""


def portal_nav(links: list[tuple[str, str]], active: str = "") -> str:
    items = []
    for label, href in links:
        css = "launch-btn launch-btn-sm" if href == active else "launch-btn-outline launch-btn-sm"
        items.append(f'<a class="{css}" href="{href}">{_h(label)}</a>')
    return PORTAL_RESPONSIVE_CSS + '<div class="portal-nav">' + "".join(items) + "</div>"


DOCTOR_NAV = [
    ("Dashboard", "/app/doctor/dashboard"),
    ("Review Queue", "/app/doctor/review"),
    ("Patients", "/app/doctor/patients"),
    ("Reports", "/app/reports"),
    ("Critical", "/app/reports/critical"),
    ("Workbench", "/app/doctor"),
]

PATIENT_NAV = [
    ("Dashboard", "/app/patient/dashboard"),
    ("History", "/app/patient/history"),
    ("Reports", "/app/patient/reports"),
    ("Orders", "/app/patient/orders"),
    ("Invoices", "/app/patient/invoices"),
    ("Profile", "/app/patient/profile"),
    ("QR Card", "/app/patient/qr"),
    ("Notifications", "/app/patient/notifications"),
]
