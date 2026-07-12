import { APP_URL, IS_PRODUCTION } from "@/lib/constants";
import { isPublicSiteHost } from "@/lib/domains";

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

/**
 * Sign-in URL: on production marketing hosts, route to the app subdomain.
 */
export function loginUrl(host?: string | null): string {
  if (!IS_PRODUCTION) return "/login";
  if (isPublicSiteHost(host)) {
    return `${APP_URL.replace(/\/$/, "")}/login`;
  }
  return "/login";
}

/**
 * Absolute app path for cross-domain navigation from marketing host.
 */
export function appPathUrl(path: string, host?: string | null): string {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  if (IS_PRODUCTION && isPublicSiteHost(host)) {
    return `${APP_URL.replace(/\/$/, "")}${normalized}`;
  }
  return normalized;
}

export function bookDemoUrl(host?: string | null): string {
  if (IS_PRODUCTION && isPublicSiteHost(host)) {
    return `${APP_URL.replace(/\/$/, "")}/book-demo`;
  }
  return "/book-demo";
}
