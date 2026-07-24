import { apiRequest } from "@/services/api";
import { ApiError } from "@/lib/errors";

export type RoleDashboardAuth = {
  token?: string | null;
  organizationId?: string | null;
  collectorId?: string | null;
  patientCode?: string | null;
};

export type RoleDashboardCard = {
  label: string;
  value: string;
  hint?: string;
};

export type RoleDashboardPayload = {
  role: string;
  organization_id?: string | null;
  generated_at?: string;
  metrics: Record<string, number | string | boolean | null>;
  cards: RoleDashboardCard[];
  empty?: boolean;
  pii_policy?: string;
  tenant_note?: string;
};

export type RoleDashboardKey =
  | "admin"
  | "administration"
  | "reception"
  | "laboratory"
  | "lab"
  | "collector"
  | "doctor"
  | "patient";

function opts(auth: RoleDashboardAuth, extra?: { timeoutMs?: number; signal?: AbortSignal }) {
  const headers: Record<string, string> = {};
  if (auth.collectorId) headers["X-Collector-Id"] = auth.collectorId;
  if (auth.patientCode) headers["X-Patient-Code"] = auth.patientCode;
  return {
    token: auth.token,
    organizationId: auth.organizationId,
    headers,
    timeoutMs: extra?.timeoutMs,
    signal: extra?.signal,
  };
}

async function unwrap<T>(promise: Promise<{ success?: boolean; data?: T; error?: string }>): Promise<T> {
  const body = await promise;
  if (body && body.success === false) {
    throw new ApiError(body.error || "Role dashboard request failed", 400);
  }
  if (body?.data === undefined) {
    throw new ApiError("Empty role dashboard response", 500);
  }
  return body.data;
}

export async function fetchRoleDashboard(
  role: RoleDashboardKey,
  auth: RoleDashboardAuth,
  extra?: { timeoutMs?: number; signal?: AbortSignal },
): Promise<RoleDashboardPayload> {
  return unwrap(
    apiRequest<{ success?: boolean; data?: RoleDashboardPayload; error?: string }>(
      `/api/v1/role-dashboards/${role}`,
      opts(auth, extra),
    ),
  );
}
