import { apiRequest, type ApiEnvelope } from "@/lib/api/client";
import type { WorkspaceKey } from "@/lib/workspaces";
import { workspaceByKey } from "@/lib/workspaces";

export type WorkspaceDashboard = Record<string, unknown>;

export async function fetchWorkspaceDashboard(
  key: WorkspaceKey,
  token: string,
  organizationId: string,
): Promise<WorkspaceDashboard> {
  const definition = workspaceByKey(key);
  const response = await apiRequest<ApiEnvelope<WorkspaceDashboard> | WorkspaceDashboard>(
    definition.dashboardPath,
    { token, organizationId },
  );
  if (response && typeof response === "object" && "data" in response) {
    return (response as ApiEnvelope<WorkspaceDashboard>).data;
  }
  return response as WorkspaceDashboard;
}

export async function fetchReceptionDashboard(
  token: string,
  organizationId: string,
): Promise<WorkspaceDashboard> {
  return fetchWorkspaceDashboard("reception", token, organizationId);
}

export async function fetchExecutiveDashboard(
  token: string,
  organizationId: string,
): Promise<WorkspaceDashboard> {
  return fetchWorkspaceDashboard("executive", token, organizationId);
}

export async function fetchLabDashboard(
  token: string,
  organizationId: string,
): Promise<WorkspaceDashboard> {
  return fetchWorkspaceDashboard("lab", token, organizationId);
}

export async function fetchDoctorDashboard(
  token: string,
  organizationId: string,
): Promise<WorkspaceDashboard> {
  return fetchWorkspaceDashboard("doctor", token, organizationId);
}

export async function fetchPatientDashboard(
  token: string,
  organizationId: string,
): Promise<WorkspaceDashboard> {
  return fetchWorkspaceDashboard("patient", token, organizationId);
}

export async function fetchAdminDashboard(
  token: string,
  organizationId: string,
): Promise<WorkspaceDashboard> {
  return fetchWorkspaceDashboard("admin", token, organizationId);
}

export async function fetchCollectorDashboard(
  token: string,
  organizationId: string,
): Promise<WorkspaceDashboard> {
  return fetchWorkspaceDashboard("collector", token, organizationId);
}

export async function fetchClinicDashboard(
  token: string,
  organizationId: string,
): Promise<WorkspaceDashboard> {
  return fetchWorkspaceDashboard("clinic", token, organizationId);
}
