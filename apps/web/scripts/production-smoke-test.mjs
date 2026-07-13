#!/usr/bin/env node
/**
 * DxCon environment smoke test — Release 8.1
 *
 * Usage (production):
 *   node apps/web/scripts/production-smoke-test.mjs
 *
 * Usage (staging):
 *   PUBLIC_SITE_URL=https://staging.dxcon.com.vn \
 *   APP_URL=https://app-staging.dxcon.com.vn \
 *   API_BASE_URL=https://api-staging.dxcon.com.vn \
 *   SMOKE_ENV=staging \
 *   node apps/web/scripts/production-smoke-test.mjs
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const PUBLIC_SITE_URL = process.env.PUBLIC_SITE_URL ?? "https://dxcon.com.vn";
const APP_URL = process.env.APP_URL ?? "https://app.dxcon.com.vn";
const API_BASE_URL = process.env.API_BASE_URL ?? "https://api.dxcon.com.vn";
const SMOKE_ENV = process.env.SMOKE_ENV ?? "production";
const TIMEOUT_MS = Number(process.env.TIMEOUT_MS ?? 15000);
const REPORT_PATH =
  process.env.SMOKE_REPORT_PATH ??
  path.resolve(__dirname, "../../generated-release/STAGING_SMOKE_REPORT.json");

const APP_HOST = new URL(APP_URL).hostname;
const IS_PRODUCTION_SMOKE = SMOKE_ENV === "production";

const results = [];

function record(name, pass, detail = "") {
  results.push({ name, pass, detail, environment: SMOKE_ENV });
  const icon = pass ? "PASS" : "FAIL";
  console.log(`  [${icon}] ${name}${detail ? ` — ${detail}` : ""}`);
}

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
      redirect: "manual",
      headers: {
        "User-Agent": "DxCon-SmokeTest/8.1",
        ...(options.headers ?? {}),
      },
    });
  } finally {
    clearTimeout(timer);
  }
}

async function fetchFollow(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(url, {
      ...options,
      signal: controller.signal,
      redirect: "follow",
      headers: {
        "User-Agent": "DxCon-SmokeTest/8.1",
        ...(options.headers ?? {}),
      },
    });
  } finally {
    clearTimeout(timer);
  }
}

async function testPublicHome() {
  try {
    const res = await fetchFollow(`${PUBLIC_SITE_URL}/`);
    const body = await res.text();
    const pass =
      res.status === 200 &&
      (body.includes("DxCon") || body.includes("dxcon") || body.length > 500);
    record("public.home.200", pass, `status=${res.status}`);
  } catch (e) {
    record("public.home.200", false, String(e));
  }
}

async function testWwwRedirect() {
  if (!IS_PRODUCTION_SMOKE) {
    record("public.www_redirect", true, "skipped (non-production smoke)");
    return;
  }
  try {
    const res = await fetchWithTimeout("https://www.dxcon.com.vn/");
    const location = res.headers.get("location") ?? "";
    const pass =
      (res.status === 301 || res.status === 308) && location.includes("dxcon.com.vn");
    record("public.www_redirect", pass, `status=${res.status} location=${location}`);
  } catch (e) {
    record("public.www_redirect", false, String(e));
  }
}

async function testPublicPages() {
  for (const route of ["/services", "/partners", "/pricing", "/contact"]) {
    try {
      const res = await fetchFollow(`${PUBLIC_SITE_URL}${route}`);
      record(`public.page${route}`, res.status === 200, `status=${res.status}`);
    } catch (e) {
      record(`public.page${route}`, false, String(e));
    }
  }
}

async function testLoginLinkTargetsApp() {
  try {
    const res = await fetchWithTimeout(`${PUBLIC_SITE_URL}/login`);
    const location = res.headers.get("location") ?? "";
    const pass =
      (res.status === 301 || res.status === 302 || res.status === 307 || res.status === 308) &&
      location.includes(APP_HOST) &&
      location.includes("/login");
    record("public.login_redirects_to_app", pass, `status=${res.status} location=${location}`);
  } catch (e) {
    record("public.login_redirects_to_app", false, String(e));
  }
}

async function testAppLogin() {
  try {
    const res = await fetchFollow(`${APP_URL}/login`);
    record("app.login.200", res.status === 200, `status=${res.status}`);
  } catch (e) {
    record("app.login.200", false, String(e));
  }
}

async function testUnauthenticatedAppRedirect() {
  try {
    const res = await fetchWithTimeout(`${APP_URL}/app`);
    const location = res.headers.get("location") ?? "";
    const pass =
      (res.status === 301 || res.status === 302 || res.status === 307 || res.status === 308) &&
      location.includes("/login");
    record("app.unauthenticated_redirect", pass, `status=${res.status} location=${location}`);
  } catch (e) {
    record("app.unauthenticated_redirect", false, String(e));
  }
}

async function testAppRoleRoutesNo500() {
  for (const route of ["/app/patient", "/app/lab", "/app/doctor"]) {
    try {
      const res = await fetchWithTimeout(`${APP_URL}${route}`);
      record(`app.route_no500${route}`, res.status !== 500, `status=${res.status}`);
    } catch (e) {
      record(`app.route_no500${route}`, false, String(e));
    }
  }
}

async function testApiHealth() {
  try {
    const res = await fetchFollow(`${API_BASE_URL}/api/v1/system/health`);
    const edgeBlocked = res.status === 403;
    record(
      "api.health",
      res.status === 200,
      edgeBlocked
        ? `status=403 (edge/WAF block — not application auth)`
        : `status=${res.status}`,
    );
  } catch (e) {
    record("api.health", false, String(e));
  }
}

async function testApiCorsAllowed() {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/api/v1/system/health`, {
      headers: { Origin: APP_URL },
    });
    const acao = res.headers.get("access-control-allow-origin") ?? "";
    record("api.cors_allowed_origin", acao === APP_URL, `status=${res.status} ACAO=${acao}`);
  } catch (e) {
    record("api.cors_allowed_origin", false, String(e));
  }
}

async function testApiCorsDenied() {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/api/v1/system/health`, {
      headers: { Origin: "https://evil.attacker.example" },
    });
    const acao = res.headers.get("access-control-allow-origin") ?? "";
    record("api.cors_denied_origin", !acao, `status=${res.status} ACAO=${acao || "(none)"}`);
  } catch (e) {
    record("api.cors_denied_origin", false, String(e));
  }
}

async function testApiAuthRejection() {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/api/v1/auth/me`);
    record("api.auth_rejection", res.status === 401, `status=${res.status}`);
  } catch (e) {
    record("api.auth_rejection", false, String(e));
  }
}

function writeReport() {
  const passed = results.filter((r) => r.pass).length;
  const failed = results.filter((r) => !r.pass).length;
  const payload = {
    generated_at: new Date().toISOString(),
    environment: SMOKE_ENV,
    targets: { PUBLIC_SITE_URL, APP_URL, API_BASE_URL },
    summary: { passed, failed, total: results.length },
    results,
  };
  fs.mkdirSync(path.dirname(REPORT_PATH), { recursive: true });
  fs.writeFileSync(REPORT_PATH, JSON.stringify(payload, null, 2));
  console.log(`\nReport: ${REPORT_PATH}`);
}

async function main() {
  console.log(`DxCon Smoke Test (${SMOKE_ENV})`);
  console.log(`  PUBLIC_SITE_URL=${PUBLIC_SITE_URL}`);
  console.log(`  APP_URL=${APP_URL}`);
  console.log(`  API_BASE_URL=${API_BASE_URL}`);
  console.log("");

  await testPublicHome();
  await testWwwRedirect();
  await testPublicPages();
  await testLoginLinkTargetsApp();
  await testAppLogin();
  await testUnauthenticatedAppRedirect();
  await testAppRoleRoutesNo500();
  await testApiHealth();
  await testApiCorsAllowed();
  await testApiCorsDenied();
  await testApiAuthRejection();

  const passed = results.filter((r) => r.pass).length;
  const failed = results.filter((r) => !r.pass).length;
  console.log(`\nResults: ${passed} passed, ${failed} failed, ${results.length} total`);
  writeReport();

  if (failed > 0) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Smoke test runner error:", err);
  process.exit(1);
});
