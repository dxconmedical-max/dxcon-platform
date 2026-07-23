import { APP_ENV, APP_URL, IS_PRODUCTION } from "@/lib/constants";
import { hostFromUrl, isPublicSiteHost, normalizeHost } from "@/lib/domains";

/**
 * Returns a safe relative path for post-login redirects.
 * Rejects absolute URLs and protocol-relative paths.
 */
export function safeRedirectPath(
  next: string | null | undefined,
  fallback = "/app",
): string {
  if (!next) return fallback;
  if (!next.startsWith("/") || next.startsWith("//")) return fallback;
  if (next.includes("://")) return fallback;
  return next;
}

function usesSplitDomains(): boolean {
  return IS_PRODUCTION || APP_ENV === "staging";
}

/** True when APP_URL is on a different host than the current request host. */
function appHostDiffersFrom(host?: string | null): boolean {
  const current = normalizeHost(host);
  const appHost = hostFromUrl(APP_URL);
  return Boolean(current && appHost && current !== appHost);
}

/**
 * Sign-in URL: on split-domain marketing hosts, route to APP_URL.
 * When APP_URL shares the current host (unified apex), keep a relative path.
 */
export function loginUrl(host?: string | null): string {
  if (!usesSplitDomains()) return "/login";
  if (isPublicSiteHost(host) && appHostDiffersFrom(host)) {
    return `${APP_URL.replace(/\/$/, "")}/login`;
  }
  return "/login";
}

/**
 * Absolute app path for cross-domain navigation from marketing host.
 */
export function appPathUrl(path: string, host?: string | null): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (usesSplitDomains() && isPublicSiteHost(host) && appHostDiffersFrom(host)) {
    return `${APP_URL.replace(/\/$/, "")}${normalized}`;
  }
  return normalized;
}

export function bookDemoUrl(host?: string | null): string {
  if (usesSplitDomains() && isPublicSiteHost(host) && appHostDiffersFrom(host)) {
    return `${APP_URL.replace(/\/$/, "")}/book-demo`;
  }
  return "/book-demo";
}
