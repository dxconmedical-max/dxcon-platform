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

function checkFiles() {
  const required = [
    "src/lib/workspaces.ts",
    "src/lib/api/workspaces.ts",
    "src/components/layout/RoleWorkspacePanel.tsx",
    "src/components/layout/RoleWorkspace.tsx",
    "src/components/layout/AppWorkspaceRedirect.tsx",
    "src/components/providers/AuthProvider.tsx",
    "src/app/app/page.tsx",
    "src/app/app/admin/page.tsx",
    "src/app/app/reception/page.tsx",
    "src/app/app/doctor/page.tsx",
    "src/app/app/lab/page.tsx",
    "src/app/app/collector/page.tsx",
    "src/app/app/clinic/page.tsx",
    "src/app/app/patient/page.tsx",
    "src/app/app/executive/page.tsx",
  ];
  checks.required_files = required.every((f) => fs.existsSync(path.join(root, f)));
}

function checkWorkspaceRegistry() {
  const content = fs.readFileSync(path.join(root, "src/lib/workspaces.ts"), "utf8");
  const paths = [
    "/api/v1/reception/workspace/dashboard",
    "/api/v1/lab/workspace/dashboard",
    "/api/v1/portal/doctor/dashboard",
    "/api/v1/portal/patient/dashboard",
    "/api/v1/executive-platform/dashboard",
    "/api/v1/dashboard/admin",
    "/api/v1/dashboard/collector",
    "/api/v1/clinic/dashboard",
  ];
  checks.workspace_api_paths = paths.every((p) => content.includes(p));
}

function checkRolePagesUseShell() {
  const rolePages = [
    "src/app/app/admin/page.tsx",
    "src/app/app/reception/page.tsx",
    "src/app/app/doctor/page.tsx",
  ];
  checks.role_workspace_component = rolePages.every((f) =>
    fs.readFileSync(path.join(root, f), "utf8").includes("RoleWorkspace"),
  );
}

function checkAppRedirect() {
  const content = fs.readFileSync(path.join(root, "src/app/app/page.tsx"), "utf8");
  checks.app_workspace_redirect = content.includes("AppWorkspaceRedirect");
}

function checkAuthRestore() {
  const content = fs.readFileSync(
    path.join(root, "src/components/providers/AuthProvider.tsx"),
    "utf8",
  );
  checks.session_restore_on_app_routes =
    content.includes("restoreSession") && content.includes('pathname.startsWith("/app")');
}

async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(8000) });
    checks.external_api_health = { ok: response.ok, status: response.status };
  } catch (error) {
    checks.external_api_health = { ok: false, warning: String(error), status: "WARNING" };
  }
}

checkFiles();
checkWorkspaceRegistry();
checkRolePagesUseShell();
checkAppRedirect();
checkAuthRestore();
await checkHealth();

const failed = Object.entries(checks).filter(([key, v]) => {
  if (key === "external_api_health" && v?.status === "WARNING") return false;
  return v === false || v?.ok === false;
});
const status = failed.length === 0 ? "PASS" : "FAIL";

writeReport("RELEASE_6_AUTH_SHELL_REPORT.json", {
  release: "6.0",
  sprint: "Authentication + Application Shell + Role Workspace",
  branch: "release/6.0-auth-shell",
  status,
  checks,
  workspaces: [
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

console.log(`Release 6.0 auth shell verification: ${status}`);
if (status === "FAIL") process.exit(1);
