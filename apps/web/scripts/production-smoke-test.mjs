#!/usr/bin/env node
/**
 * DxCon Production Smoke Test — Release 8.1 Sprint 9
 *
 * Verifies public website, application host, and API health without credentials.
 *
 * Usage:
 *   node apps/web/scripts/production-smoke-test.mjs
 *
 * Environment overrides:
 *   PUBLIC_SITE_URL  (default: https://dxcon.com.vn)
 *   APP_URL          (default: https://app.dxcon.com.vn)
 *   API_BASE_URL     (default: https://api.dxcon.com.vn)
 *   TIMEOUT_MS       (default: 15000)
 */

const PUBLIC_SITE_URL = process.env.PUBLIC_SITE_URL ?? "https://dxcon.com.vn";
const APP_URL = process.env.APP_URL ?? "https://app.dxcon.com.vn";
const API_BASE_URL = process.env.API_BASE_URL ?? "https://api.dxcon.com.vn";
const TIMEOUT_MS = Number(process.env.TIMEOUT_MS ?? 15000);

const results = [];

function record(name, pass, detail = "") {
  results.push({ name, pass, detail });
  const icon = pass ? "PASS" : "FAIL";
  console.log(`  [${icon}] ${name}${detail ? ` — ${detail}` : ""}`);
}

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(url, { ...options, signal: controller.signal, redirect: "manual" });
  } finally {
    clearTimeout(timer);
  }
}

async function fetchFollow(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(url, { ...options, signal: controller.signal, redirect: "follow" });
  } finally {
    clearTimeout(timer);
  }
}

// --- Public website tests ---

async function testPublicHome() {
  try {
    const res = await fetchFollow(`${PUBLIC_SITE_URL}/`);
    const body = await res.text();
    const hasContent = res.status === 200 && (body.includes("DxCon") || body.includes("dxcon") || body.length > 500);
    record("public.home.200", hasContent, `status=${res.status}`);
  } catch (e) {
    record("public.home.200", false, String(e));
  }
}

async function testWwwRedirect() {
  try {
    const res = await fetchWithTimeout("https://www.dxcon.com.vn/");
    const location = res.headers.get("location") ?? "";
    const pass = (res.status === 301 || res.status === 308) && location.includes("dxcon.com.vn");
    record("public.www_redirect", pass, `status=${res.status} location=${location}`);
  } catch (e) {
    record("public.www_redirect", false, String(e));
  }
}

async function testPublicPages() {
  for (const path of ["/services", "/partners", "/pricing", "/contact", "/privacy", "/terms"]) {
    try {
      const res = await fetchFollow(`${PUBLIC_SITE_URL}${path}`);
      record(`public.page${path}`, res.status === 200, `status=${res.status}`);
    } catch (e) {
      record(`public.page${path}`, false, String(e));
    }
  }
}

async function testLoginLinkTargetsApp() {
  try {
    const res = await fetchWithTimeout(`${PUBLIC_SITE_URL}/login`);
    const location = res.headers.get("location") ?? "";
    const pass =
      (res.status === 301 || res.status === 302 || res.status === 307 || res.status === 308) &&
      location.includes("app.dxcon.com.vn") &&
      location.includes("/login");
    record("public.login_redirects_to_app", pass, `status=${res.status} location=${location}`);
  } catch (e) {
    record("public.login_redirects_to_app", false, String(e));
  }
}

// --- Application host tests ---

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

async function testAppStatusPages() {
  for (const path of ["/service-unavailable", "/forbidden", "/session-expired"]) {
    try {
      const res = await fetchFollow(`${APP_URL}${path}`);
      record(`app.page${path}`, res.status === 200, `status=${res.status}`);
    } catch (e) {
      record(`app.page${path}`, false, String(e));
    }
  }
}

// --- API tests ---

async function testApiHealth() {
  try {
    const res = await fetchFollow(`${API_BASE_URL}/api/v1/system/health`);
    record("api.health", res.status === 200, `status=${res.status}`);
  } catch (e) {
    record("api.health", false, String(e));
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

async function testApiCorsPreflight() {
  try {
    const res = await fetchWithTimeout(`${API_BASE_URL}/api/v1/system/health`, {
      method: "OPTIONS",
      headers: {
        Origin: APP_URL,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization,Content-Type",
      },
    });
    const acao = res.headers.get("access-control-allow-origin") ?? "";
    const pass = (res.status === 200 || res.status === 204) && acao.length > 0;
    record("api.cors_preflight", pass, `status=${res.status} ACAO=${acao}`);
  } catch (e) {
    record("api.cors_preflight", false, String(e));
  }
}

async function testApiNo500OnSmokeRoutes() {
  const routes = [
    "/api/v1/system/health",
    "/api/v1/system/version",
    "/api/v1/auth/me",
  ];
  for (const route of routes) {
    try {
      const res = await fetchWithTimeout(`${API_BASE_URL}${route}`);
      record(`api.no500${route}`, res.status !== 500, `status=${res.status}`);
    } catch (e) {
      record(`api.no500${route}`, false, String(e));
    }
  }
}

// --- Main ---

async function main() {
  console.log("DxCon Production Smoke Test");
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
  await testAppStatusPages();
  await testApiHealth();
  await testApiAuthRejection();
  await testApiCorsPreflight();
  await testApiNo500OnSmokeRoutes();

  const passed = results.filter((r) => r.pass).length;
  const failed = results.filter((r) => !r.pass).length;
  console.log("");
  console.log(`Results: ${passed} passed, ${failed} failed, ${results.length} total`);

  if (failed > 0) {
    console.log("\nFailed checks:");
    for (const r of results.filter((r) => !r.pass)) {
      console.log(`  - ${r.name}: ${r.detail}`);
    }
    process.exit(1);
  }
  console.log("\nAll smoke tests passed.");
}

main().catch((err) => {
  console.error("Smoke test runner error:", err);
  process.exit(1);
});
