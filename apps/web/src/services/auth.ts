import { apiRequest } from "@/services/api";
import {
  parseCapabilitiesResponse,
  parseMeResponse,
} from "@/lib/auth/session";

export type AuthUser = {
  id: string;
  email: string;
  role: string;
  phone?: string | null;
  organization_id?: string | null;
  is_active?: boolean;
};

export type Membership = {
  membership_id: string | null;
  organization_id: string;
  organization_name: string;
  organization_type: string;
  organization_code: string;
  organization_status: string;
  role_code: string;
  membership_status: string;
  default_workspace: string;
  department_id?: string | null;
  team_id?: string | null;
};

export type Organization = {
  id: string;
  organization_code: string;
  organization_name: string;
  organization_type: string;
  status: string;
};

export type AuthCapabilities = {
  user: AuthUser;
  organization: Organization | null;
  membership: {
    membership_id: string | null;
    organization_id: string | null;
    role_code: string | null;
    membership_status: string | null;
    department_id?: string | null;
    team_id?: string | null;
  };
  workspace: string;
  default_workspace: string;
  permissions: string[];
  features: string[];
};

export type MeResponse = {
  user: AuthUser;
  active_organization_id: string | null;
  memberships: Membership[];
  requires_organization_selection: boolean;
};

export type LoginResponse = {
  success: boolean;
  token: string;
  access_token: string;
  refresh_token: string;
  email: string;
  role: string;
  user: AuthUser;
};

type ApiEnvelope<T> = { success: boolean; data: T };

export async function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  console.debug("[services/auth.login] POST /api/v1/auth/login");
  // Raw payload — authStore parses/validates via parseLoginResponse.
  return apiRequest<LoginResponse>("/api/v1/auth/login", {
    method: "POST",
    body: { email, password },
  });
}

export async function refreshAccessToken(
  refreshToken: string,
): Promise<{ access_token: string; token: string }> {
  const response = await apiRequest<{
    access_token: string;
    token: string;
  }>("/api/v1/auth/refresh", {
    method: "POST",
    refreshToken,
  });
  return response;
}

export async function logout(refreshToken: string): Promise<void> {
  await apiRequest("/api/v1/auth/logout", {
    method: "POST",
    refreshToken,
  });
}

export async function fetchMe(token: string): Promise<MeResponse> {
  const response = await apiRequest<unknown>("/api/v1/auth/me", {
    token,
  });
  return parseMeResponse(response) as MeResponse;
}

export async function fetchMemberships(token: string): Promise<Membership[]> {
  const response = await apiRequest<ApiEnvelope<Membership[]>>(
    "/api/v1/auth/memberships",
    { token },
  );
  return response.data;
}

export async function switchOrganization(
  token: string,
  organizationId: string,
): Promise<AuthCapabilities> {
  const response = await apiRequest<unknown>(
    "/api/v1/auth/switch-organization",
    {
      method: "POST",
      token,
      body: { organization_id: organizationId },
    },
  );
  return parseCapabilitiesResponse(response) as AuthCapabilities;
}

export async function fetchCapabilities(
  token: string,
  organizationId?: string | null,
): Promise<AuthCapabilities> {
  const query = organizationId
    ? `?organization_id=${encodeURIComponent(organizationId)}`
    : "";
  const response = await apiRequest<unknown>(
    `/api/v1/auth/capabilities${query}`,
    { token, organizationId },
  );
  return parseCapabilitiesResponse(response) as AuthCapabilities;
}

export async function forgotPassword(email: string): Promise<string> {
  const response = await apiRequest<{ success: boolean; message: string }>(
    "/api/v1/auth/forgot-password",
    { method: "POST", body: { email } },
  );
  return response.message;
}

export async function resetPassword(
  token: string,
  password: string,
): Promise<void> {
  await apiRequest("/api/v1/auth/reset-password", {
    method: "POST",
    body: { token, password },
  });
}
