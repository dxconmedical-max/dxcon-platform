/**
 * Runtime and build-time environment configuration.
 * Production builds fail when required variables are missing or invalid.
 */

export type AppEnvironment = "development" | "staging" | "production";

const REQUIRED_PUBLIC_VARS = [
  "NEXT_PUBLIC_API_BASE_URL",
  "NEXT_PUBLIC_PUBLIC_SITE_URL",
  "NEXT_PUBLIC_APP_URL",
  "NEXT_PUBLIC_APP_ENV",
] as const;

function readEnv(key: string): string | undefined {
  const value = process.env[key];
  return value && value.trim() !== "" ? value.trim() : undefined;
}

function isLocalhostUrl(url: string): boolean {
  try {
    const host = new URL(url).hostname;
    return host === "localhost" || host === "127.0.0.1" || host.endsWith(".local");
  } catch {
    return false;
  }
}

export function collectEnvErrors(): string[] {
  const errors: string[] = [];
  const appEnv = (readEnv("NEXT_PUBLIC_APP_ENV") ?? "development") as AppEnvironment;
  const isProduction = appEnv === "production";
  const isStaging = appEnv === "staging";
  const isDeployed = isProduction || isStaging;

  for (const key of REQUIRED_PUBLIC_VARS) {
    if (!readEnv(key)) {
      errors.push(`Missing ${key}`);
    }
  }

  const demoMode = (readEnv("NEXT_PUBLIC_DEMO_MODE") ?? "false").toLowerCase() === "true";
  if (isProduction && demoMode) {
    errors.push("NEXT_PUBLIC_DEMO_MODE must be false in production");
  }
  if (isStaging && demoMode) {
    errors.push("NEXT_PUBLIC_DEMO_MODE must be false in staging (use pilot accounts)");
  }

  if (isDeployed) {
    const apiBase = readEnv("NEXT_PUBLIC_API_BASE_URL");
    const publicSite = readEnv("NEXT_PUBLIC_PUBLIC_SITE_URL");
    const appUrl = readEnv("NEXT_PUBLIC_APP_URL");
    const label = isProduction ? "production" : "staging";

    if (apiBase && isLocalhostUrl(apiBase)) {
      errors.push(`NEXT_PUBLIC_API_BASE_URL must not use localhost in ${label}`);
    }
    if (publicSite && isLocalhostUrl(publicSite)) {
      errors.push(`NEXT_PUBLIC_PUBLIC_SITE_URL must not use localhost in ${label}`);
    }
    if (appUrl && isLocalhostUrl(appUrl)) {
      errors.push(`NEXT_PUBLIC_APP_URL must not use localhost in ${label}`);
    }
    if (apiBase) {
      try {
        const host = new URL(apiBase).hostname.toLowerCase();
        if (
          host === "api.example.com" ||
          host === "example.com" ||
          host.endsWith(".example.com")
        ) {
          errors.push(
            `NEXT_PUBLIC_API_BASE_URL must not use example.com hosts in ${label}`,
          );
        }
        if (isProduction && host !== "api.dxcon.com.vn") {
          errors.push(
            "NEXT_PUBLIC_API_BASE_URL must be https://api.dxcon.com.vn in production",
          );
        }
      } catch {
        errors.push(`NEXT_PUBLIC_API_BASE_URL is not a valid URL in ${label}`);
      }
    }
  }

  return errors;
}

export function assertProductionEnv(): void {
  const errors = collectEnvErrors();
  if (errors.length > 0) {
    throw new Error(
      `Environment validation failed:\n${errors.map((e) => `  - ${e}`).join("\n")}`,
    );
  }
}

const appEnv = (readEnv("NEXT_PUBLIC_APP_ENV") ?? "development") as AppEnvironment;
const isProduction = appEnv === "production";
const isStaging = appEnv === "staging";

if (isProduction || isStaging) {
  assertProductionEnv();
}

export const env = {
  apiBaseUrl: readEnv("NEXT_PUBLIC_API_BASE_URL") ?? (isProduction || isStaging ? "" : "http://localhost:5000"),
  publicSiteUrl:
    readEnv("NEXT_PUBLIC_PUBLIC_SITE_URL") ??
    (isProduction || isStaging ? "" : "http://localhost:3000"),
  appUrl: readEnv("NEXT_PUBLIC_APP_URL") ?? (isProduction || isStaging ? "" : "http://localhost:3000"),
  appEnv,
  demoMode: (readEnv("NEXT_PUBLIC_DEMO_MODE") ?? "false").toLowerCase() === "true",
  isProduction,
  isStaging,
} as const;

export type PublicEnv = typeof env;
