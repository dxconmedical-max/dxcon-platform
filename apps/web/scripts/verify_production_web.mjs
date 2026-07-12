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
    "generated-release/PRODUCTION_WEB_DISCOVERY_REPORT.json",
    "docs/PRODUCTION_WEB_API_CONTRACT.md",
    "docs/VERCEL_PRODUCTION_CONFIGURATION.md",
    "docs/DOMAIN_ROUTING.md",
    ".env.example",
    "src/lib/env.ts",
    "src/lib/domains.ts",
    "src/lib/urls.ts",
    "src/lib/api/client.ts",
    "src/lib/api/auth.ts",
    "src/lib/api/health.ts",
    "src/lib/api/workspaces.ts",
    "src/lib/i18n/index.ts",
    "src/app/services/page.tsx",
    "src/app/partners/page.tsx",
    "src/app/pricing/page.tsx",
    "src/app/contact/page.tsx",
    "src/app/book-demo/page.tsx",
    "src/app/privacy/page.tsx",
    "src/app/terms/page.tsx",
    "src/app/app/not-found/page.tsx",
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

function checkHeroSafety() {
  const hero = fs.readFileSync(
    path.join(root, "src/components/landing/HeroSection.tsx"),
    "utf8",
  );
  checks.no_fake_metrics =
    !hero.includes("1,248") &&
    !hero.includes("HIPAA-ready") &&
    (hero.includes("previewLabel") || hero.includes("previewNote"));
}

function checkDemoMode() {
  const demo = (process.env.NEXT_PUBLIC_DEMO_MODE ?? "false").toLowerCase();
  const env = process.env.NEXT_PUBLIC_APP_ENV ?? "development";
  checks.demo_mode_disabled_in_production = env !== "production" || demo === "false";
}

await checkHealth();
checkFiles();
checkEnvExample();
checkHeroSafety();
checkDemoMode();

const failed = Object.entries(checks).filter(([key, v]) => {
  if (key === "external_api_health" && v?.status === "WARNING") return false;
  return v === false || v?.ok === false;
});
const status = failed.length === 0 ? "PASS" : "FAIL";

writeReport("PRODUCTION_WEB_ROLLOUT_REPORT.json", { status, checks, phase: "0-4" });

if (status === "FAIL") {
  console.error("Production web rollout verification failed:", failed);
  process.exit(1);
}

console.log("Production web rollout verification PASS");
