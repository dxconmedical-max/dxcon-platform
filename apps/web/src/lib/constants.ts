import { env } from "@/lib/env";

export const API_BASE_URL = env.apiBaseUrl;
export const PUBLIC_SITE_URL = env.publicSiteUrl;
export const APP_URL = env.appUrl;
export const APP_ENV = env.appEnv;
export const DEMO_MODE = env.demoMode;
export const IS_PRODUCTION = env.isProduction;
export const IS_STAGING = env.isStaging;

export const APP_NAME = "DxCon";

export const AUTH_COOKIE = "dxcon_authenticated";
export const ROLE_COOKIE = "dxcon_role";
export const ORG_COOKIE = "dxcon_organization_id";

export const API_TIMEOUT_MS = 30_000;

export const PUBLIC_MARKETING_ROUTES = [
  "/",
  "/services",
  "/solutions",
  "/partners",
  "/pricing",
  "/contact",
  "/book-demo",
  "/privacy",
  "/terms",
] as const;

export const PUBLIC_APP_ROUTES = [
  "/login",
  "/register",
  "/logout",
  "/forgot-password",
  "/reset-password",
  "/session-expired",
  "/service-unavailable",
  "/forbidden",
  "/onboarding/register",
] as const;

export const PUBLIC_ROUTES = [
  ...PUBLIC_MARKETING_ROUTES,
  ...PUBLIC_APP_ROUTES,
] as const;

export const REQUIRED_ENV_VARS = [
  "NEXT_PUBLIC_API_BASE_URL",
  "NEXT_PUBLIC_PUBLIC_SITE_URL",
  "NEXT_PUBLIC_APP_URL",
  "NEXT_PUBLIC_APP_ENV",
] as const;

export { collectEnvErrors as validateProductionEnv } from "@/lib/env";
