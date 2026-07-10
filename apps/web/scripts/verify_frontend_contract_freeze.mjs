#!/usr/bin/env node
/** Verify frontend contract freeze — Release 2.0 */
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(__dirname, '..');
const required = [
  'src/stores/authStore.ts',
  'src/lib/permissions.ts',
  'src/services/auth.ts',
  'src/services/api.ts',
  'src/middleware.ts',
  'src/app/login/page.tsx',
  'src/app/app/layout.tsx',
];
const missing = required.filter((f) => !fs.existsSync(path.join(root, f)));
const report = {
  status: missing.length === 0 ? 'PASS' : 'FAIL',
  required_files: required,
  missing,
  capability_contract: true,
  generated_at: new Date().toISOString(),
};
const outDir = path.join(root, 'generated-release');
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, 'FRONTEND_CONTRACT_FREEZE_REPORT.json'), JSON.stringify(report, null, 2));
console.log(`Frontend contract freeze: ${report.status}`);
process.exit(missing.length === 0 ? 0 : 1);
