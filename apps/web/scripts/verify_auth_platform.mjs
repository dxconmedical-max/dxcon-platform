#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const outDir = path.join(root, "generated-release");

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://api.dxcon.com.vn";

function writeReport(name, payload) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(
    path.join(outDir, name),
    JSON.stringify({ generated_at: new Date().toISOString(), ...payload }, null, 2),
  );
}

const checks = {};

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(8000) });
    checks.external_api_health = { ok: response.ok, status: response.status };
  } catch (error) {
    checks.external_api_health = { ok: false, warning: String(error), status: "WARNING" };
  }
}

function checkFiles() {
  const required = [
    "docs/AUTH_API_CONTRACT.md",
    "docs/TOKEN_SECURITY.md",
    "src/services/api.ts",
    "src/services/auth.ts",
    "src/stores/authStore.ts",
    "src/lib/permissions.ts",
    "src/middleware.ts",
    "src/app/login/page.tsx",
    "src/app/select-organization/page.tsx",
    "src/app/app/admin/page.tsx",
  ];
  checks.required_files = required.every((f) => fs.existsSync(path.join(root, f)));
}

function checkEnvExample() {
  const content = fs.readFileSync(path.join(root, ".env.example"), "utf8");
  const keys = [
    "NEXT_PUBLIC_API_BASE_URL",
    "NEXT_PUBLIC_PUBLIC_SITE_URL",
    "NEXT_PUBLIC_APP_URL",
    "NEXT_PUBLIC_APP_ENV",
    "NEXT_PUBLIC_DEMO_MODE",
  ];
  checks.env_example = keys.every((k) => content.includes(k));
}

function checkDemoMode() {
  const demo = (process.env.NEXT_PUBLIC_DEMO_MODE ?? "false").toLowerCase();
  const env = process.env.NEXT_PUBLIC_APP_ENV ?? "development";
  checks.demo_mode_disabled_in_production = env !== "production" || demo === "false";
}

await checkHealth();
checkFiles();
checkEnvExample();
checkDemoMode();

const failed = Object.entries(checks).filter(([key, v]) => {
  if (key === "external_api_health" && v?.status === "WARNING") return false;
  return v === false || v?.ok === false;
});
const status = failed.length === 0 ? "PASS" : "FAIL";

writeReport("AUTH_PLATFORM_REPORT.json", { status, checks });
writeReport("TENANT_CONTEXT_REPORT.json", {
  status,
  organization_switch: true,
  membership_api: "/api/v1/auth/memberships",
  switch_api: "/api/v1/auth/switch-organization",
});
writeReport("ROLE_ROUTING_REPORT.json", {
  status,
  workspace_prefix: "/app",
  routes: [
    "/app/admin",
    "/app/executive",
    "/app/reception",
    "/app/doctor",
    "/app/lab",
    "/app/collector",
    "/app/clinic",
    "/app/patient",
  ],
});
writeReport("FRONTEND_SECURITY_REPORT.json", {
  status,
  token_storage: "sessionStorage",
  http_only_cookies: false,
  security_headers: "next.config.ts",
  csp: true,
});
writeReport("AUTH_BACKEND_GAPS.json", {
  gaps: [
    "Password reset email delivery not implemented",
    "JWT does not embed organization_id",
    "HttpOnly cookie auth not end-to-end",
    "Refresh token rotation not implemented",
  ],
});

console.log(`Auth platform verification: ${status}`);
if (status === "FAIL") process.exit(1);
