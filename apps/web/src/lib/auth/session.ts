import { ApiError } from "@/lib/errors";

export type AuthUser = {
  id: string;
  email: string;
  role: string;
  phone?: string | null;
  organization_id?: string | null;
  is_active?: boolean;
};

/** Validated session payload after login / refresh. */
export type ValidatedLoginSession = {
  accessToken: string;
  refreshToken: string;
  email: string;
  role: string;
  user: AuthUser;
};

function asRecord(value: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}

function asNonEmptyString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function parseUser(raw: unknown, fallbackRole: string | null): AuthUser | null {
  const obj = asRecord(raw);
  if (!obj) return null;
  const id = asNonEmptyString(obj.id) ?? asNonEmptyString(obj.user_id);
  const email = asNonEmptyString(obj.email);
  const role =
    asNonEmptyString(obj.role) ??
    asNonEmptyString(obj.role_code) ??
    fallbackRole;
  if (!id || !email || !role) return null;
  return {
    id,
    email,
    role,
    phone: (obj.phone as string | null | undefined) ?? null,
    organization_id:
      (obj.organization_id as string | null | undefined) ?? null,
    is_active:
      typeof obj.is_active === "boolean" ? obj.is_active : undefined,
  };
}

/**
 * Parse backend login payloads without assuming a single envelope shape.
 * Accepts flat `{ access_token, refresh_token, user, ... }` and
 * `{ success, data: { ... } }` variants.
 */
export function parseLoginResponse(payload: unknown): ValidatedLoginSession {
  const root = asRecord(payload);
  if (!root) {
    throw new ApiError("Malformed login response", 502, {
      code: "MALFORMED_LOGIN_RESPONSE",
    });
  }

  const data = asRecord(root.data) ?? root;
  const accessToken =
    asNonEmptyString(data.access_token) ?? asNonEmptyString(data.token);
  const refreshToken = asNonEmptyString(data.refresh_token);
  const email = asNonEmptyString(data.email);
  const role = asNonEmptyString(data.role);
  const user = parseUser(data.user, role);

  if (!accessToken || !refreshToken || !user) {
    throw new ApiError("Malformed login response", 502, {
      code: "MALFORMED_LOGIN_RESPONSE",
      missing: {
        accessToken: !accessToken,
        refreshToken: !refreshToken,
        user: !user,
      },
    });
  }

  return {
    accessToken,
    refreshToken,
    email: email ?? user.email,
    role: role ?? user.role,
    user,
  };
}

/** Transient keys that must never survive persist / migration. */
export const TRANSIENT_AUTH_KEYS = [
  "status",
  "error",
  "isHydrated",
  "isLoading",
  "isInitializingSession",
  "isSubmittingLogin",
  "isRefreshingSession",
  "memberships",
  "capabilities",
] as const;

export const AUTH_PERSIST_VERSION = 3;
export const AUTH_STORAGE_KEY = "dxcon-auth-v3";
/** Legacy keys to clear on migrate so old loading state cannot revive. */
export const LEGACY_AUTH_STORAGE_KEYS = [
  "dxcon-auth",
  "dxcon-auth-v1",
  "dxcon-auth-v2",
] as const;
