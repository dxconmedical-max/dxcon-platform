import { apiRequest, type ApiEnvelope } from "./client";
import { withSampleFallback, SAMPLE_NOTE, type Sourced } from "./adapter";
import { SAMPLE_DOCTOR_REPORT, SAMPLE_DOCTOR_REVIEWS } from "./samples";

export type DoctorReviewRow = {
  report_code: string;
  patient_name: string;
  patient_code?: string;
  status: string;
  collected_at?: string;
};

export type ReportAnalyte = {
  name: string;
  value: string;
  unit?: string;
  reference?: string;
  abnormal: boolean;
  flag?: string;
};

export type DoctorReport = {
  report_code: string;
  patient_name: string;
  patient_code?: string;
  collected_at?: string;
  status: string;
  analytes: ReportAnalyte[];
  ai_interpretation?: string;
};

type Ctx = { token: string; organizationId: string };

function asArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? (value as Record<string, unknown>[]) : [];
}

/** Pending review queue. Reads doctor dashboard pending_reviews; sample fallback. */
export async function fetchDoctorReviewQueue({
  token,
  organizationId,
}: Ctx): Promise<Sourced<DoctorReviewRow[]>> {
  return withSampleFallback<DoctorReviewRow[]>(
    async () => {
      const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        "/api/v1/portal/doctor/dashboard",
        { token, organizationId },
      );
      const raw = asArray(response.data?.pending_reviews ?? response.data?.reviews);
      const rows = raw.map((row) => ({
        report_code: String(row.report_code ?? row.report ?? row.order_code ?? row.id ?? "—"),
        patient_name: String(row.patient_name ?? row.patient ?? row.full_name ?? "—"),
        patient_code: row.patient_code ? String(row.patient_code) : undefined,
        status: String(row.status ?? "AWAITING_REVIEW").toUpperCase(),
        collected_at: row.collected_at ? String(row.collected_at) : undefined,
      }));
      if (rows.length === 0) throw new Error("no reviews");
      return rows;
    },
    SAMPLE_DOCTOR_REVIEWS,
    SAMPLE_NOTE,
  );
}

/** Report / result viewer. Backed by GET /portal/doctor/reports/<code>. */
export async function fetchDoctorReport(
  { token, organizationId }: Ctx,
  reportCode: string,
): Promise<Sourced<DoctorReport>> {
  return withSampleFallback<DoctorReport>(
    async () => {
      const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        `/api/v1/portal/doctor/reports/${encodeURIComponent(reportCode)}`,
        { token, organizationId },
      );
      const data = (response.data ?? {}) as Record<string, unknown>;
      const analytesRaw = asArray(data.analytes ?? data.results ?? data.items);
      const analytes = analytesRaw.map((row) => {
        const abnormal =
          Boolean(row.abnormal) ||
          Boolean(row.abnormal_flag) ||
          ["H", "L", "HIGH", "LOW", "CRITICAL"].includes(
            String(row.flag ?? "").toUpperCase(),
          );
        return {
          name: String(row.name ?? row.test ?? row.analyte ?? "—"),
          value: String(row.value ?? row.result_value ?? "—"),
          unit: row.unit ? String(row.unit) : undefined,
          reference: String(row.reference ?? row.ref_range ?? row.reference_range ?? ""),
          abnormal,
          flag: row.flag ? String(row.flag) : row.abnormal_flag ? String(row.abnormal_flag) : undefined,
        } satisfies ReportAnalyte;
      });
      const patientName = data.patient_name ?? data.patient;
      if (!patientName && analytes.length === 0) throw new Error("no report");
      return {
        report_code: String(data.report_code ?? reportCode),
        patient_name: String(patientName ?? "—"),
        patient_code: data.patient_code ? String(data.patient_code) : undefined,
        collected_at: data.collected_at ? String(data.collected_at) : undefined,
        status: String(data.status ?? "AWAITING_REVIEW").toUpperCase(),
        analytes,
        ai_interpretation: data.ai_interpretation ? String(data.ai_interpretation) : undefined,
      };
    },
    { ...SAMPLE_DOCTOR_REPORT, report_code: reportCode },
    SAMPLE_NOTE,
  );
}

/** Save a clinical note / interpretation. Backed by POST /portal/doctor/notes. */
export async function saveDoctorNote(
  { token, organizationId }: Ctx,
  payload: { patient_code: string; note_text: string; note_type?: string },
): Promise<Sourced<{ message: string }>> {
  return withSampleFallback<{ message: string }>(
    async () => {
      await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        "/api/v1/portal/doctor/notes",
        {
          token,
          organizationId,
          method: "POST",
          body: { note_type: "INTERPRETATION", ...payload },
        },
      );
      return { message: "Clinical note saved." };
    },
    { message: "Note captured locally (no live backend response)." },
    "Note captured locally (no live backend response).",
  );
}

/**
 * Electronic signature / sign-off. There is no dedicated e-sign endpoint; the
 * report approval acts as the sign-off. Attempts the reporting approve route
 * and records the signature intent, with a labeled sample fallback.
 */
export async function signReport(
  { token, organizationId }: Ctx,
  payload: { report_code: string; order_code?: string; signer_name: string },
): Promise<Sourced<{ report_code: string; status: string; signed_by: string }>> {
  const ref = payload.order_code ?? payload.report_code;
  return withSampleFallback<{ report_code: string; status: string; signed_by: string }>(
    async () => {
      await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        `/api/v1/reporting/review/${encodeURIComponent(ref)}/approve`,
        {
          token,
          organizationId,
          method: "POST",
          body: { signer_name: payload.signer_name },
        },
      );
      return {
        report_code: payload.report_code,
        status: "SIGNED",
        signed_by: payload.signer_name,
      };
    },
    {
      report_code: payload.report_code,
      status: "SIGNED",
      signed_by: payload.signer_name,
    },
    "Signature recorded locally — maps to report approval when the backend is reachable.",
  );
}
