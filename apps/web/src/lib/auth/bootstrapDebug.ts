import { AUTH_COOKIE } from "@/lib/constants";

/** Read-only cookie probe for bootstrap diagnostics — never mutates cookies. */
export function readCookieAuthenticated(): boolean {
  if (typeof document === "undefined") return false;
  return document.cookie
    .split(";")
    .map((part) => part.trim())
    .some((part) => part === `${AUTH_COOKIE}=1`);
}

export type AuthBootstrapLog = {
  status: string;
  bootstrapPhase: string;
  pathname?: string;
  sessionAuthenticated: boolean;
  redirectReason?: string | null;
  hasToken?: boolean;
  hasCapabilities?: boolean;
};

/**
 * Structured Gate 1 bootstrap trace. Keep payloads free of token values.
 */
export function logAuthBootstrap(
  source: string,
  fields: AuthBootstrapLog,
): void {
  if (typeof console === "undefined") return;
  console.info(`[auth-bootstrap:${source}]`, {
    status: fields.status,
    bootstrapPhase: fields.bootstrapPhase,
    pathname: fields.pathname ?? null,
    cookieAuthenticated: readCookieAuthenticated(),
    sessionAuthenticated: fields.sessionAuthenticated,
    redirectReason: fields.redirectReason ?? null,
    hasToken: fields.hasToken ?? null,
    hasCapabilities: fields.hasCapabilities ?? null,
  });
}
