#!/usr/bin/env node
/**
 * Auth module freeze guard — ensures freeze docs + frozen files +
 * mandatory regression suites remain present. Does not change runtime auth.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(webRoot, "..", "..");

const freezeDoc = path.join(repoRoot, "docs", "AUTH_FREEZE.md");

const frozenFiles = [
  "src/stores/authStore.ts",
  "src/lib/auth/session.ts",
  "src/lib/auth/bootstrapDebug.ts",
  "src/lib/cookies.ts",
  "src/services/auth.ts",
  "src/components/providers/AuthProvider.tsx",
  "src/components/providers/AuthErrorBoundary.tsx",
  "src/hooks/useAuth.ts",
  "src/components/layout/AppShell.tsx",
  "src/middleware.ts",
  "src/app/login/page.tsx",
  "src/app/layout.tsx",
];

const requiredTests = [
  "src/app/login/page.test.tsx",
  "src/stores/authStore.login.test.ts",
  "src/components/providers/AuthProvider.test.tsx",
  "src/components/layout/AppShell.test.tsx",
  "src/components/layout/AdminBootstrap.integration.test.tsx",
  "src/hooks/useRequireAuth.bootstrap.test.tsx",
  "src/hooks/gate1Auth.regression.test.tsx",
  "src/lib/auth/session.test.ts",
  "src/services/api.auth.test.ts",
  "src/auth/e2e.login.hardening.test.ts",
];

function existsRel(rel) {
  return fs.existsSync(path.join(webRoot, rel));
}

const missingFrozen = frozenFiles.filter((f) => !existsRel(f));
const missingTests = requiredTests.filter((f) => !existsRel(f));
const freezeDocOk = fs.existsSync(freezeDoc);

const freezeDocText = freezeDocOk ? fs.readFileSync(freezeDoc, "utf8") : "";
const freezeDocMentionsReview =
  freezeDocOk &&
  /dedicated regression (review|approval)/i.test(freezeDocText) &&
  /bootstrapPhase/i.test(freezeDocText);
const freezeDocHasPersistence =
  freezeDocOk &&
  /session persistence strategy/i.test(freezeDocText) &&
  /sessionStorage/i.test(freezeDocText) &&
  /dxcon-auth-v3/i.test(freezeDocText);
const freezeDocHasRouteGuards =
  freezeDocOk &&
  /route-guard behavior/i.test(freezeDocText) &&
  /useRequireAuth/i.test(freezeDocText);

const report = {
  status:
    freezeDocOk &&
    freezeDocMentionsReview &&
    freezeDocHasPersistence &&
    freezeDocHasRouteGuards &&
    missingFrozen.length === 0 &&
    missingTests.length === 0
      ? "PASS"
      : "FAIL",
  freeze_doc: "docs/AUTH_FREEZE.md",
  freeze_doc_present: freezeDocOk,
  freeze_doc_mentions_review: freezeDocMentionsReview,
  freeze_doc_has_persistence: freezeDocHasPersistence,
  freeze_doc_has_route_guards: freezeDocHasRouteGuards,
  frozen_files: frozenFiles,
  missing_frozen_files: missingFrozen,
  required_tests: requiredTests,
  missing_tests: missingTests,
  generated_at: new Date().toISOString(),
};

const outDir = path.join(webRoot, "generated-release");
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(
  path.join(outDir, "AUTH_FREEZE_GUARD_REPORT.json"),
  JSON.stringify(report, null, 2),
);

console.log(`Auth freeze guard: ${report.status}`);
if (report.status !== "PASS") {
  if (!freezeDocOk) console.error("Missing docs/AUTH_FREEZE.md");
  if (!freezeDocMentionsReview) {
    console.error("docs/AUTH_FREEZE.md missing required freeze policy text");
  }
  if (!freezeDocHasPersistence) {
    console.error(
      "docs/AUTH_FREEZE.md missing Session persistence strategy (sessionStorage / dxcon-auth-v3)",
    );
  }
  if (!freezeDocHasRouteGuards) {
    console.error("docs/AUTH_FREEZE.md missing Route-guard behavior section");
  }
  if (missingFrozen.length) {
    console.error("Missing frozen files:", missingFrozen.join(", "));
  }
  if (missingTests.length) {
    console.error("Missing required tests:", missingTests.join(", "));
  }
  process.exit(1);
}
