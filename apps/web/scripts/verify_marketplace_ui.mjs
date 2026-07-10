#!/usr/bin/env node
/** Verify Marketplace UI — Epic 5 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");
const pages = [
  "src/app/marketplace/page.tsx",
  "src/app/marketplace/tests/page.tsx",
  "src/app/marketplace/packages/page.tsx",
  "src/app/marketplace/providers/page.tsx",
  "src/app/marketplace/providers/[id]/page.tsx",
  "src/app/marketplace/compare/page.tsx",
  "src/app/marketplace/book/page.tsx",
  "src/app/marketplace/checkout/page.tsx",
  "src/app/marketplace/payment/page.tsx",
  "src/app/app/patient/bookings/page.tsx",
  "src/app/app/patient/payments/page.tsx",
];
const missing = pages.filter((p) => !fs.existsSync(path.join(root, p)));
const report = { status: missing.length === 0 ? "PASS" : "FAIL", pages, missing, generated_at: new Date().toISOString() };
fs.mkdirSync(path.join(root, "generated-release"), { recursive: true });
fs.writeFileSync(path.join(root, "generated-release/MARKETPLACE_UI_REPORT.json"), JSON.stringify(report, null, 2));
console.log(`Marketplace UI: ${report.status}`);
process.exit(missing.length === 0 ? 0 : 1);
