#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const pages = [
  "src/app/app/admin/integrations/page.tsx",
  "src/app/app/admin/integrations/connectors/page.tsx",
  "src/app/app/admin/integrations/messages/page.tsx",
  "src/app/app/admin/integrations/exceptions/page.tsx",
  "src/app/app/admin/integrations/mappings/page.tsx",
  "src/app/app/admin/integrations/webhooks/page.tsx",
  "src/app/app/admin/integrations/health/page.tsx",
];
const ok = pages.every((p) => fs.existsSync(path.join(root, p)));
const report = { status: ok ? "PASS" : "FAIL", pages, generated_at: new Date().toISOString() };
fs.mkdirSync(path.join(root, "generated-release"), { recursive: true });
fs.writeFileSync(path.join(root, "generated-release/INTEGRATION_CENTER_UI_REPORT.json"), JSON.stringify(report, null, 2));
console.log(report.status);
process.exit(ok ? 0 : 1);
