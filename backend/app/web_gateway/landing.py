"""Production public landing page — Sprint 011."""

from __future__ import annotations

import html

from flask import url_for

from app.web.launch_ui_lib import render_page
from app.web_gateway.config import public_site_url, web_app_url


def _section(title: str, body: str, section_id: str = "") -> str:
    sid = f' id="{html.escape(section_id)}"' if section_id else ""
    return f'<section class="launch-marketing-section"{sid}><h2>{html.escape(title)}</h2>{body}</section>'


def render_production_landing() -> str:
    mark_url = url_for("static", filename="branding/dxcon-mark.svg")
    login_url = f"{web_app_url()}/login" if web_app_url() else "/login"
    body = f"""
    <div class="launch-public">
      <header class="launch-public-nav">
        <div class="launch-hero-brand">
          <img src="{html.escape(mark_url)}" alt="" width="40" height="40">
          <strong>DxCon</strong>
        </div>
        <nav class="launch-public-links">
          <a href="#solutions">Solutions</a>
          <a href="#security">Security</a>
          <a href="#contact">Contact</a>
          <a class="launch-cta launch-cta-primary launch-cta-sm" href="{html.escape(login_url)}">Sign in</a>
        </nav>
      </header>

      <div class="launch-public-inner launch-marketing-hero" id="hero">
        <h1>Healthcare operations platform for Vietnam</h1>
        <p class="launch-hero-subtitle">DxCon connects laboratories, clinics, doctors, patients, and partners on one secure SaaS platform — from order to released report.</p>
        <div class="launch-hero-cta-row">
          <a class="launch-cta launch-cta-primary" href="{html.escape(login_url)}">Sign in</a>
          <a class="launch-cta-ghost" href="#book-demo">Book demo</a>
          <a class="launch-cta-ghost" href="#contact">Contact sales</a>
        </div>
      </div>

      {_section("Product overview", '<p class="launch-hero-lead">End-to-end diagnostics workflow: reception, collection, laboratory, doctor review, reporting, billing, and patient portals — multi-tenant and audit-ready.</p>', "product")}

      {_section("Solutions", '''
        <div class="launch-marketing-grid">
          <div class="launch-marketing-card"><h3>For laboratories</h3><p>Sample accession, QC, validation, LIS connectors, and release controls.</p></div>
          <div class="launch-marketing-card"><h3>For clinics</h3><p>Partner ordering, patient registration, billing, and clinic dashboards.</p></div>
          <div class="launch-marketing-card"><h3>For doctors</h3><p>Review queue, critical results, clinical notes, and signed reports.</p></div>
          <div class="launch-marketing-card"><h3>For patients</h3><p>Released reports, invoices, QR health card, and consent management.</p></div>
        </div>
      ''', "solutions")}

      {_section("Home collection", '<p class="launch-hero-lead">Collector routing, chain of custody, GPS proof, and cold-chain monitoring for home phlebotomy networks.</p>', "home-collection")}

      {_section("Reporting", '<p class="launch-hero-lead">Versioned clinical reports, PDF-ready previews, digital signature foundation, and patient visibility guards.</p>', "reporting")}

      {_section("Partner ecosystem", '<p class="launch-hero-lead">Clinic and lab partnerships, corporate contracts, marketplace bookings, and API integrations.</p>', "partners")}

      {_section("Security", '''
        <p class="launch-hero-lead">Tenant isolation, RBAC, audit logging, encrypted sessions, and production health monitoring.</p>
        <ul class="launch-feature-list">
          <li>Role-based workspaces for every stakeholder</li>
          <li>API gateway with JWT and session dual auth</li>
          <li>Cloudflare SSL and Render production deployment</li>
        </ul>
      ''', "security")}

      <section class="launch-marketing-section" id="book-demo">
        <h2>Book demo</h2>
        <p class="launch-hero-lead">See DxCon with your laboratory or clinic workflow in a guided pilot session.</p>
        <a class="launch-cta launch-cta-primary" href="mailto:sales@dxcon.com.vn?subject=DxCon%20Demo%20Request">Request a demo</a>
      </section>

      <section class="launch-marketing-section" id="contact">
        <h2>Contact</h2>
        <p class="launch-hero-lead">Sales: <a href="mailto:sales@dxcon.com.vn">sales@dxcon.com.vn</a> · Support: <a href="mailto:support@dxcon.com.vn">support@dxcon.com.vn</a></p>
        <p class="launch-hint">Public site: {html.escape(public_site_url())} · App: {html.escape(web_app_url())}</p>
      </section>

      <footer class="launch-public-footer">
        <span>© DxCon Healthcare Platform</span>
        <a href="{html.escape(login_url)}">Sign in to workspace</a>
      </footer>
    </div>
    """
    return render_page("DxCon — Healthcare Platform", body, public=True)
