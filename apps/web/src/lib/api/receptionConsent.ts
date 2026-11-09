import { apiRequest } from "@/services/api";

export const CONSENT_TYPES = [
  "LAB_TEST",
  "PARTNER_LAB",
  "CLINIC_SHARE",
  "CONTACT",
  "OVERSEAS_STORAGE",
] as const;

export type ConsentType = (typeof CONSENT_TYPES)[number];

export type ConsentState = {
  granted: boolean;
  status: string;
  version: string | null;
  recorded_at: string | null;
} | null;

export type PatientConsents = {
  patient_code: string;
  required: ConsentType;
  consents: Record<ConsentType, ConsentState>;
};

export type RecordConsentsBody = {
  consents: { consent_type: ConsentType; granted: boolean }[];
  method: "PAPER" | "ELECTRONIC";
  document_ref?: string;
  guardian?: { name: string; relationship: string; document: string };
};

type Ctx = { token: string; organizationId?: string | null };

function opts(ctx: Ctx, extra: Record<string, unknown> = {}) {
  return {
    token: ctx.token,
    organizationId: ctx.organizationId ?? null,
    timeoutMs: 30_000,
    ...extra,
  };
}

function path(patientCode: string): string {
  return `/api/v1/reception/workspace/patients/${encodeURIComponent(patientCode)}/consents`;
}

/** GET — latest consent state per type (null = never recorded). */
export async function getPatientConsents(ctx: Ctx, patientCode: string): Promise<PatientConsents> {
  const response = await apiRequest<{ success: boolean; data: PatientConsents }>(
    path(patientCode),
    opts(ctx),
  );
  return response.data;
}

/** POST — append consent decisions; the latest row per type wins. */
export async function recordPatientConsents(
  ctx: Ctx,
  patientCode: string,
  body: RecordConsentsBody,
): Promise<PatientConsents> {
  const response = await apiRequest<{ success: boolean; data: PatientConsents }>(
    path(patientCode),
    opts(ctx, { method: "POST", body }),
  );
  return response.data;
}
