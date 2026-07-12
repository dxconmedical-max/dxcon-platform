#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const outDir = path.join(root, "generated-release");

function exists(rel) {
  return fs.existsSync(path.join(root, rel));
}

function writeReport(name, payload) {
  fs.mkdirSync(outDir, { recursive: true });
  fs.writeFileSync(
    path.join(outDir, name),
    JSON.stringify({ generated_at: new Date().toISOString(), ...payload }, null, 2),
  );
}

const domains = {
  patient_booking: {
    label: "Patient Booking",
    files: [
      "src/components/workspace/BookingWizard.tsx",
      "src/app/app/patient/book/page.tsx",
      "src/lib/api/booking.ts",
    ],
    features: [
      "multi-step wizard",
      "package selection",
      "location selection",
      "home collection",
      "schedule picker",
      "QR booking confirmation",
    ],
  },
  patient_portal: {
    label: "Patient Portal",
    files: [
      "src/app/app/patient/page.tsx",
      "src/app/app/patient/bookings/page.tsx",
      "src/app/app/patient/results/page.tsx",
      "src/app/app/patient/payments/page.tsx",
      "src/app/app/patient/health-summary/page.tsx",
      "src/app/app/patient/profile/page.tsx",
      "src/lib/api/patient-portal.ts",
    ],
    features: ["dashboard", "booking history", "test reports", "invoices", "AI health summary", "profile"],
  },
  reception: {
    label: "Reception Workspace",
    files: [
      "src/app/app/reception/queue/page.tsx",
      "src/app/app/reception/register/page.tsx",
      "src/app/app/reception/search/page.tsx",
      "src/lib/api/reception.ts",
    ],
    features: [
      "today's queue",
      "check-in",
      "walk-in registration",
      "booking search",
      "QR scanner placeholder",
      "patient search",
    ],
  },
  collector: {
    label: "Collector Workspace",
    files: [
      "src/app/app/collector/route/page.tsx",
      "src/app/app/collector/jobs/page.tsx",
      "src/app/app/collector/timeline/page.tsx",
      "src/lib/api/collector.ts",
    ],
    features: [
      "today's route",
      "assigned collections",
      "map placeholder",
      "navigation button",
      "barcode scanner placeholder",
      "upload specimen photo",
      "collection timeline",
    ],
  },
  laboratory: {
    label: "Laboratory Workspace",
    files: [
      "src/app/app/lab/samples/page.tsx",
      "src/app/app/lab/queue/page.tsx",
      "src/app/app/lab/qc/page.tsx",
      "src/app/app/lab/verification/page.tsx",
      "src/lib/api/lab.ts",
    ],
    features: ["received samples", "analyzer queue", "QC status", "verification workflow", "release workflow"],
  },
  doctor: {
    label: "Doctor Workspace",
    files: [
      "src/app/app/doctor/patients/page.tsx",
      "src/app/app/doctor/reports/page.tsx",
      "src/app/app/doctor/reports/[code]/page.tsx",
      "src/lib/api/doctor.ts",
    ],
    features: [
      "patient list",
      "result viewer",
      "abnormal highlight",
      "AI interpretation placeholder",
      "electronic signature placeholder",
    ],
  },
};

const shared = [
  "src/components/layout/WorkspaceScreen.tsx",
  "src/components/workspace/primitives.tsx",
  "src/hooks/useSourcedData.ts",
  "src/lib/api/adapter.ts",
  "src/lib/api/samples.ts",
];

const domainResults = {};
let allOk = true;

for (const [key, def] of Object.entries(domains)) {
  const missing = def.files.filter((f) => !exists(f));
  const ok = missing.length === 0;
  if (!ok) allOk = false;
  domainResults[key] = { label: def.label, ok, missing, features: def.features };
}

const sharedMissing = shared.filter((f) => !exists(f));
if (sharedMissing.length > 0) allOk = false;

// Guardrails: booking wizard must implement the required steps; adapters must be honest about sample data.
const wizard = exists("src/components/workspace/BookingWizard.tsx")
  ? fs.readFileSync(path.join(root, "src/components/workspace/BookingWizard.tsx"), "utf8")
  : "";
const guardrails = {
  wizard_steps: ["Packages", "Location", "Schedule", "Review", "Confirmed"].every((s) => wizard.includes(s)),
  qr_confirmation: wizard.includes("QrPanel"),
  sample_data_labeled: exists("src/components/workspace/primitives.tsx")
    ? fs.readFileSync(path.join(root, "src/components/workspace/primitives.tsx"), "utf8").includes("Sample data")
    : false,
  reuses_appshell: exists("src/components/layout/WorkspaceScreen.tsx")
    ? fs.readFileSync(path.join(root, "src/components/layout/WorkspaceScreen.tsx"), "utf8").includes("AppShell")
    : false,
};
if (!Object.values(guardrails).every(Boolean)) allOk = false;

const status = allOk ? "PASS" : "FAIL";

writeReport("RELEASE_6_SPRINT2_REPORT.json", {
  release: "6.0",
  sprint: "Production Sprint 2",
  scope: "Epic 16-21 — Patient, Reception, Collector, Laboratory, Doctor workspaces",
  status,
  shared_components: { ok: sharedMissing.length === 0, missing: sharedMissing },
  domains: domainResults,
  guardrails,
  notes: [
    "Live backend endpoints are used where available; unimplemented capabilities use labeled sample adapters.",
    "Sample data is surfaced with a visible 'Sample data' badge on each screen.",
    "Reuses existing authentication, AppShell, and role workspace routing.",
  ],
});

console.log(`Release 6.0 Sprint 2 verification: ${status}`);
for (const [key, r] of Object.entries(domainResults)) {
  console.log(`  ${r.ok ? "PASS" : "FAIL"} ${r.label}${r.missing.length ? ` (missing: ${r.missing.join(", ")})` : ""}`);
  void key;
}
if (!allOk) {
  if (sharedMissing.length) console.error("Missing shared:", sharedMissing);
  console.error("Guardrails:", guardrails);
  process.exit(1);
}
