import { apiRequest, type ApiEnvelope } from "./client";
import { withSampleFallback, SAMPLE_NOTE, type Sourced } from "./adapter";
import {
  SAMPLE_INVOICES,
  SAMPLE_PROFILE,
  SAMPLE_HEALTH_SUMMARY,
  SAMPLE_PATIENT_BOOKINGS,
} from "./samples";

export type PatientBooking = {
  reference: string;
  service: string;
  scheduled_at: string;
  location: string;
  status: string;
};

export type PatientInvoice = {
  invoice_no: string;
  issued_at: string;
  amount: number;
  currency: string;
  status: string;
  description?: string;
};

export type PatientProfile = {
  full_name: string;
  patient_code: string;
  date_of_birth?: string;
  gender?: string;
  phone?: string;
  email?: string;
  address?: string;
  blood_type?: string;
};

export type HealthSummary = {
  generated_at: string;
  headline: string;
  highlights: string[];
  recommendation: string;
};

type Ctx = { token: string; organizationId: string };

function asArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value) ? (value as Record<string, unknown>[]) : [];
}

/** Booking history. Attempts patient portal history; sample fallback. */
export async function fetchPatientBookings({
  token,
  organizationId,
}: Ctx): Promise<Sourced<PatientBooking[]>> {
  return withSampleFallback<PatientBooking[]>(
    async () => {
      const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        "/api/v1/portal/patient/history?event_type=booking",
        { token, organizationId },
      );
      const raw = asArray(response.data?.events ?? response.data?.bookings);
      const bookings = raw.map((row) => ({
        reference: String(row.reference ?? row.booking_reference ?? row.id ?? "—"),
        service: String(row.service ?? row.package ?? row.description ?? "—"),
        scheduled_at: String(row.scheduled_at ?? row.date ?? "—"),
        location: String(row.location ?? row.branch ?? "—"),
        status: String(row.status ?? "—"),
      }));
      if (bookings.length === 0) throw new Error("no bookings");
      return bookings;
    },
    SAMPLE_PATIENT_BOOKINGS,
    SAMPLE_NOTE,
  );
}

/** Invoices. Backed by GET /api/v1/portal/patient/invoices; sample fallback. */
export async function fetchPatientInvoices({
  token,
  organizationId,
}: Ctx): Promise<Sourced<PatientInvoice[]>> {
  return withSampleFallback<PatientInvoice[]>(
    async () => {
      const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        "/api/v1/portal/patient/invoices",
        { token, organizationId },
      );
      const raw = asArray(response.data?.invoices ?? response.data);
      const invoices = raw.map((row) => ({
        invoice_no: String(row.invoice_no ?? row.invoice_number ?? row.id ?? "—"),
        issued_at: String(row.issued_at ?? row.created_at ?? row.date ?? "—"),
        amount: typeof row.amount === "number" ? row.amount : Number(row.amount) || 0,
        currency: String(row.currency ?? "VND"),
        status: String(row.status ?? "—"),
        description: row.description ? String(row.description) : undefined,
      }));
      if (invoices.length === 0) throw new Error("no invoices");
      return invoices;
    },
    SAMPLE_INVOICES,
    SAMPLE_NOTE,
  );
}

/** Patient profile. Read via dashboard payload; sample fallback. */
export async function fetchPatientProfile({
  token,
  organizationId,
}: Ctx): Promise<Sourced<PatientProfile>> {
  return withSampleFallback<PatientProfile>(
    async () => {
      const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        "/api/v1/portal/patient/dashboard",
        { token, organizationId },
      );
      const p = (response.data?.profile ?? response.data?.patient ?? {}) as Record<string, unknown>;
      const fullName = p.full_name ?? p.name;
      if (!fullName) throw new Error("no profile");
      return {
        full_name: String(fullName),
        patient_code: String(p.patient_code ?? p.code ?? "—"),
        date_of_birth: p.date_of_birth ? String(p.date_of_birth) : undefined,
        gender: p.gender ? String(p.gender) : undefined,
        phone: p.phone ? String(p.phone) : undefined,
        email: p.email ? String(p.email) : undefined,
        address: p.address ? String(p.address) : undefined,
        blood_type: p.blood_type ? String(p.blood_type) : undefined,
      };
    },
    SAMPLE_PROFILE,
    SAMPLE_NOTE,
  );
}

/** Update patient profile. Attempts PUT; returns updated echo on success. */
export async function updatePatientProfile(
  { token, organizationId }: Ctx,
  patch: Partial<PatientProfile>,
): Promise<Sourced<PatientProfile>> {
  return withSampleFallback<PatientProfile>(
    async () => {
      const response = await apiRequest<ApiEnvelope<Record<string, unknown>>>(
        "/api/v1/portal/patient/profile",
        { token, organizationId, method: "PUT", body: patch },
      );
      const p = (response.data ?? {}) as Record<string, unknown>;
      return {
        full_name: String(p.full_name ?? patch.full_name ?? SAMPLE_PROFILE.full_name),
        patient_code: String(p.patient_code ?? patch.patient_code ?? SAMPLE_PROFILE.patient_code),
        date_of_birth: (p.date_of_birth as string) ?? patch.date_of_birth,
        gender: (p.gender as string) ?? patch.gender,
        phone: (p.phone as string) ?? patch.phone,
        email: (p.email as string) ?? patch.email,
        address: (p.address as string) ?? patch.address,
        blood_type: (p.blood_type as string) ?? patch.blood_type,
      };
    },
    { ...SAMPLE_PROFILE, ...patch } as PatientProfile,
    SAMPLE_NOTE,
  );
}

/**
 * AI health summary. No patient-facing AI narrative endpoint is mounted in the
 * backend, so this is a labeled sample adapter that must be reviewed by a
 * clinician before being treated as clinical guidance.
 */
export async function fetchHealthSummary(_ctx: Ctx): Promise<Sourced<HealthSummary>> {
  void _ctx;
  return { value: SAMPLE_HEALTH_SUMMARY, source: "sample", note: SAMPLE_NOTE };
}
