#!/usr/bin/env node
/**
 * Staging frontend/API smoke test — Release 9.0
 *
 * Defaults target staging hosts. Override with env vars.
 *
 *   PUBLIC_SITE_URL=https://staging.dxcon.com.vn \
 *   APP_URL=https://app-staging.dxcon.com.vn \
 *   API_BASE_URL=https://api-staging.dxcon.com.vn \
 *   node apps/web/scripts/staging-smoke-test.mjs
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const PUBLIC_SITE_URL = process.env.PUBLIC_SITE_URL ?? "https://staging.dxcon.com.vn";
const APP_URL = process.env.APP_URL ?? "https://app-staging.dxcon.com.vn";
const API_BASE_URL = process.env.API_BASE_URL ?? "https://api-staging.dxcon.com.vn";
const TIMEOUT_MS = Number(process.env.TIMEOUT_MS ?? 20000);
const REPORT_PATH =
  process.env.SMOKE_REPORT_PATH ??
  path.resolve(__dirname, "../../../generated-release/STAGING_FRONTEND_SMOKE_REPORT.json");

const APP_HOST = new URL(APP_URL).hostname;
const results = [];

function record(name, pass, detail = "") {
  results.push({ name, pass, detail });
  console.log(`  [${pass ? "PASS" : "FAIL"}] ${name}${detail ? ` — ${detail}` : ""}`);
}

async function req(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
      redirect: options.redirect ?? "manual",
      headers: {
        "User-Agent": "DxCon-StagingSmoke/9.0",
        ...(options.headers ?? {}),
      },
    });
  } finally {
    clearTimeout(timer);
  }
}

async function main() {
  console.log("DxCon Staging Smoke Test");
  console.log(`  PUBLIC_SITE_URL=${PUBLIC_SITE_URL}`);
  console.log(`  APP_URL=${APP_URL}`);
  console.log(`  API_BASE_URL=${API_BASE_URL}\n`);

  try {
    const home = await req(`${PUBLIC_SITE_URL}/`, { redirect: "follow" });
    const body = await home.text();
    record(
      "public.home.200",
      home.status === 200 && (body.includes("DxCon") || body.length > 200),
      `status=${home.status}`,
    );
  } catch (e) {
    record("public.home.200", false, String(e));
  }

  for (const route of ["/services", "/partners"]) {
    try {
      const res = await req(`${PUBLIC_SITE_URL}${route}`, { redirect: "follow" });
      record(`public.page${route}_no500`, res.status !== 500, `status=${res.status}`);
    } catch (e) {
      record(`public.page${route}_no500`, false, String(e));
    }
  }

  try {
    const res = await req(`${PUBLIC_SITE_URL}/login`);
    const location = res.headers.get("location") ?? "";
    const pass =
      [301, 302, 307, 308].includes(res.status) &&
      location.includes(APP_HOST) &&
      location.includes("/login");
    record("public.signin_targets_app_staging", pass, `status=${res.status} location=${location}`);
  } catch (e) {
    record("public.signin_targets_app_staging", false, String(e));
  }

  try {
    const res = await req(`${APP_URL}/login`, { redirect: "follow" });
    record("app.login.200", res.status === 200, `status=${res.status}`);
  } catch (e) {
    record("app.login.200", false, String(e));
  }

  try {
    const res = await req(`${APP_URL}/app`);
    const location = res.headers.get("location") ?? "";
    record(
      "app.unauthenticated_redirect",
      [301, 302, 307, 308].includes(res.status) && location.includes("/login"),
      `status=${res.status} location=${location}`,
    );
  } catch (e) {
    record("app.unauthenticated_redirect", false, String(e));
  }

  for (const route of ["/forbidden", "/session-expired"]) {
    try {
      const res = await req(`${APP_URL}${route}`, { redirect: "follow" });
      record(`app.page${route}`, res.status === 200, `status=${res.status}`);
    } catch (e) {
      record(`app.page${route}`, false, String(e));
    }
  }

  for (const route of ["/app/patient", "/app/lab", "/app/doctor", "/app/admin"]) {
    try {
      const res = await req(`${APP_URL}${route}`);
      const cache = (res.headers.get("cache-control") || "").toLowerCase();
      record(`app.route_no500${route}`, res.status !== 500, `status=${res.status}`);
      if (res.status === 200) {
        record(
          `app.not_public_cache${route}`,
          cache.includes("private") || cache.includes("no-store") || cache === "",
          `cache-control=${cache || "(none)"}`,
        );
      }
    } catch (e) {
      record(`app.route_no500${route}`, false, String(e));
    }
  }

  try {
    const res = await req(`${API_BASE_URL}/api/v1/system/health`, { redirect: "follow" });
    record("api.health", res.status === 200, `status=${res.status}`);
    if (res.status === 403) {
      record("api.no_blanket_edge_403", false, "403 on public health — possible edge/WAF");
    } else {
      record("api.no_blanket_edge_403", true, `status=${res.status}`);
    }
  } catch (e) {
    record("api.health", false, String(e));
  }

  try {
    const res = await req(`${API_BASE_URL}/api/v1/system/health`, {
      headers: { Origin: APP_URL },
    });
    const acao = res.headers.get("access-control-allow-origin") ?? "";
    record("api.cors_allowed", acao === APP_URL, `ACAO=${acao}`);
  } catch (e) {
    record("api.cors_allowed", false, String(e));
  }

  try {
    const res = await req(`${API_BASE_URL}/api/v1/system/health`, {
      headers: { Origin: "https://evil.attacker.example" },
    });
    const acao = res.headers.get("access-control-allow-origin") ?? "";
    record("api.cors_denied", !acao, `ACAO=${acao || "(none)"}`);
  } catch (e) {
    record("api.cors_denied", false, String(e));
  }

  try {
    const res = await req(`${API_BASE_URL}/api/v1/auth/me`);
    record("api.auth_rejection", res.status === 401 || res.status === 403, `status=${res.status}`);
  } catch (e) {
    record("api.auth_rejection", false, String(e));
  }

  const passed = results.filter((r) => r.pass).length;
  const failed = results.filter((r) => !r.pass).length;
  const payload = {
    generated_at: new Date().toISOString(),
    environment: "staging",
    targets: { PUBLIC_SITE_URL, APP_URL, API_BASE_URL },
    summary: { passed, failed, total: results.length },
    results,
  };
  fs.mkdirSync(path.dirname(REPORT_PATH), { recursive: true });
  fs.writeFileSync(REPORT_PATH, JSON.stringify(payload, null, 2));
  console.log(`\nResults: ${passed} passed, ${failed} failed`);
  console.log(`Report: ${REPORT_PATH}`);
  process.exit(failed ? 1 : 0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
