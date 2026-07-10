export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://api.dxcon.com.vn";

export const PUBLIC_SITE_URL =
  process.env.NEXT_PUBLIC_PUBLIC_SITE_URL ?? "https://dxcon.com.vn";

export const APP_URL =
  process.env.NEXT_PUBLIC_APP_URL ?? "https://app.dxcon.com.vn";

export const APP_ENV = process.env.NEXT_PUBLIC_APP_ENV ?? "development";

export const DEMO_MODE =
  (process.env.NEXT_PUBLIC_DEMO_MODE ?? "false").toLowerCase() === "true";

export const IS_PRODUCTION = APP_ENV === "production";

export const APP_NAME = "DxCon";

export const AUTH_COOKIE = "dxcon_authenticated";
export const ROLE_COOKIE = "dxcon_role";
export const ORG_COOKIE = "dxcon_organization_id";

export const API_TIMEOUT_MS = 30_000;

export const PUBLIC_ROUTES = [
  "/",
  "/login",
  "/logout",
  "/forgot-password",
  "/reset-password",
  "/session-expired",
  "/service-unavailable",
  "/onboarding/register",
] as const;

export const REQUIRED_ENV_VARS = [
  "NEXT_PUBLIC_API_BASE_URL",
  "NEXT_PUBLIC_PUBLIC_SITE_URL",
  "NEXT_PUBLIC_APP_URL",
  "NEXT_PUBLIC_APP_ENV",
] as const;

export function validateProductionEnv(): string[] {
  const missing: string[] = [];
  for (const key of REQUIRED_ENV_VARS) {
    if (!process.env[key]) {
      missing.push(key);
    }
  }
  if (IS_PRODUCTION && DEMO_MODE) {
    missing.push("NEXT_PUBLIC_DEMO_MODE must be false in production");
  }
  return missing;
}
