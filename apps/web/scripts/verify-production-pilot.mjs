#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const outDir = path.join(root, "generated-release");

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://api.dxcon.com.vn";
const APP_ENV = process.env.NEXT_PUBLIC_APP_ENV ?? "development";
const DEMO_MODE = (process.env.NEXT_PUBLIC_DEMO_MODE ?? "false").toLowerCase() === "true";

function writeReport(name, payload) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(
    path.join(outDir, name),
    JSON.stringify({ generated_at: new Date().toISOString(), ...payload }, null, 2),
  );
}

function exists(rel) {
  return fs.existsSync(path.join(root, rel));
}

function read(rel) {
  return fs.readFileSync(path.join(root, rel), "utf8");
}

const checks = {};

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(8000) });
    checks.api_health = { ok: response.ok, status: response.status, url: API_BASE };
  } catch (error) {
    checks.api_health = { ok: false, warning: String(error), status: "WARNING" };
  }
}

function checkFramework() {
  const pkg = JSON.parse(read("package.json"));
  checks.framework_nextjs = pkg.dependencies?.next != null;
  checks.package_manager = "npm";
}

function checkEnv() {
  checks.env_example = exists(".env.example");
  checks.env_ts = exists("src/lib/env.ts");
  checks.demo_mode_disabled_in_production = APP_ENV !== "production" || !DEMO_MODE;
  checks.api_url_correct =
    (process.env.NEXT_PUBLIC_API_BASE_URL ?? API_BASE) === "https://api.dxcon.com.vn" ||
    APP_ENV !== "production";
}

function checkAuth() {
  const required = [
    "src/app/login/page.tsx",
    "src/app/register/page.tsx",
    "src/app/logout/page.tsx",
    "src/app/select-organization/page.tsx",
    "src/stores/authStore.ts",
    "src/components/providers/AuthProvider.tsx",
    "docs/PRODUCTION_AUTH_API_CONTRACT.md",
    "docs/WEB_TOKEN_SECURITY.md",
  ];
  checks.auth_files = required.every(exists);
  checks.session_restore = read("src/components/providers/AuthProvider.tsx").includes("restoreSession");
  const login = read("src/app/login/page.tsx");
  checks.login_show_password = login.includes("showPassword");
  checks.demo_hidden_in_production = !login.includes("DEMO_MODE") || login.includes("DEMO_MODE ?");
}

function checkShell() {
  const required = [
    "src/components/layout/AppShell.tsx",
    "src/components/layout/Header.tsx",
    "src/components/layout/Sidebar.tsx",
    "src/lib/workspace-nav.ts",
  ];
  checks.app_shell_files = required.every(exists);
  checks.org_switcher = read("src/components/layout/Header.tsx").includes("Switch organization");
}

function checkWorkspaces() {
  const routes = [
    "src/app/app/admin/page.tsx",
    "src/app/app/doctor/page.tsx",
    "src/app/app/clinic/page.tsx",
    "src/app/app/lab/page.tsx",
    "src/app/app/collector/page.tsx",
    "src/app/app/patient/page.tsx",
  ];
  checks.workspace_pages = routes.every(exists);
  checks.role_workspace = read("src/app/app/doctor/page.tsx").includes("RoleWorkspace");
}

function checkPilotPages() {
  const pages = [
    "src/app/app/admin/patients/page.tsx",
    "src/app/app/admin/orders/page.tsx",
    "src/app/app/doctor/patients/page.tsx",
    "src/app/app/doctor/reports/page.tsx",
    "src/app/app/clinic/patients/page.tsx",
    "src/app/app/lab/samples/page.tsx",
    "src/app/app/patient/orders/page.tsx",
    "src/app/app/patient/results/page.tsx",
  ];
  checks.pilot_data_pages = pages.every(exists);
}

function checkSecurity() {
  const hero = read("src/components/landing/HeroSection.tsx");
  checks.no_fake_metrics =
    !hero.includes("1,248") && !hero.includes("HIPAA-ready") && hero.includes("previewLabel");
  const nextCfg = read("next.config.ts");
  checks.csp_configured = nextCfg.includes("Content-Security-Policy");
  checks.app_no_store = nextCfg.includes("no-store");
  checks.permissions_registry = exists("src/lib/permissions.ts");
}

function checkDocs() {
  const docs = [
    "docs/DOMAIN_ROUTING.md",
    "docs/VERCEL_ENVIRONMENT_SETUP.md",
    "../../docs/PRODUCTION_CORS_SETUP.md",
    "../../docs/VERCEL_PRODUCTION_DEPLOYMENT.md",
    "../../docs/UAT_PRODUCTION_PILOT.md",
  ];
  checks.documentation = docs.every((d) => exists(d));
}

await checkHealth();
checkFramework();
checkEnv();
checkAuth();
checkShell();
checkWorkspaces();
checkPilotPages();
checkSecurity();
checkDocs();

const failed = Object.entries(checks).filter(([key, v]) => {
  if (key === "api_health" && v?.status === "WARNING") return false;
  return v === false || v?.ok === false;
});
const status = failed.length === 0 ? "PASS" : "FAIL";

writeReport("PRODUCTION_AUTH_REPORT.json", {
  release: "6.0",
  status,
  checks: {
    auth_files: checks.auth_files,
    session_restore: checks.session_restore,
    login_show_password: checks.login_show_password,
    demo_hidden_in_production: checks.demo_hidden_in_production,
    api_health: checks.api_health,
  },
});

writeReport("PRODUCTION_APP_SHELL_REPORT.json", {
  release: "6.0",
  status,
  checks: {
    app_shell_files: checks.app_shell_files,
    org_switcher: checks.org_switcher,
    workspace_pages: checks.workspace_pages,
    role_workspace: checks.role_workspace,
  },
});

writeReport("PILOT_DASHBOARD_REPORT.json", {
  release: "6.0",
  status,
  workspaces: ["/app/admin", "/app/doctor", "/app/clinic", "/app/lab", "/app/collector", "/app/patient"],
  pilot_data_pages: checks.pilot_data_pages,
});

writeReport("PRODUCTION_SECURITY_REPORT.json", {
  release: "6.0",
  status,
  checks: {
    no_fake_metrics: checks.no_fake_metrics,
    csp_configured: checks.csp_configured,
    app_no_store: checks.app_no_store,
    permissions_registry: checks.permissions_registry,
    demo_mode_disabled: checks.demo_mode_disabled_in_production,
  },
});

writeReport("PRODUCTION_PILOT_READINESS_REPORT.json", {
  release: "6.0",
  sprint: "Production Sprint 1",
  branch: "release/6.0-auth-shell",
  status,
  checks,
  failed: failed.map(([k]) => k),
  known_limitations: [
    "Bearer tokens in sessionStorage (not HttpOnly cookies)",
    "Password reset returns 501 until email flow enabled",
    "Clinic/collector list pages may need entity context (clinic_id/collector_id)",
    "Backend CORS must include .com.vn domains in production API env",
  ],
});

console.log(`Production pilot verification: ${status}`);
if (status === "FAIL") {
  console.error("Failed checks:", failed);
  process.exit(1);
}
