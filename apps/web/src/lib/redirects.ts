import { APP_URL, PUBLIC_SITE_URL } from "@/lib/constants";
import { hostFromUrl, normalizeHost } from "@/lib/domains";

/**
 * Compare two absolute URLs after normalizing protocol, hostname, port,
 * pathname, and search. Fragments are ignored.
 */
export function sameNormalizedUrl(left: string | URL, right: string | URL): boolean {
  try {
    const a = left instanceof URL ? left : new URL(left);
    const b = right instanceof URL ? right : new URL(right);
    return (
      a.protocol === b.protocol &&
      normalizeHost(a.hostname) === normalizeHost(b.hostname) &&
      a.port === b.port &&
      normalizePathname(a.pathname) === normalizePathname(b.pathname) &&
      a.search === b.search
    );
  } catch {
    return false;
  }
}

export function normalizePathname(pathname: string): string {
  if (!pathname) return "/";
  if (pathname.length > 1 && pathname.endsWith("/")) {
    return pathname.slice(0, -1);
  }
  return pathname;
}

export function originOf(url: string | URL): string {
  const parsed = url instanceof URL ? url : new URL(url);
  return parsed.origin;
}

/** Apex canonical host derived from PUBLIC_SITE_URL (never www). */
export function canonicalPublicHost(): string {
  const host = hostFromUrl(PUBLIC_SITE_URL) || "dxcon.com.vn";
  return host.startsWith("www.") ? host.slice(4) : host;
}

export function isWwwHost(host: string | null | undefined): boolean {
  const normalized = normalizeHost(host);
  // Production www is always canonical, even when unit tests use local PUBLIC_SITE_URL.
  if (normalized === "www.dxcon.com.vn") return true;
  if (!normalized.startsWith("www.")) return false;
  const apex = normalized.slice(4);
  return apex === canonicalPublicHost() || apex === hostFromUrl(PUBLIC_SITE_URL);
}

/**
 * Absolute www → apex target preserving path and query.
 * Returns null when the request is not on the www canonical host.
 * `requestHost` overrides the URL hostname when the public Host header differs
 * from the socket URL (local verification / some proxies).
 */
export function wwwToApexTarget(
  requestUrl: string | URL,
  requestHost?: string | null,
): URL | null {
  const current = requestUrl instanceof URL ? requestUrl : new URL(requestUrl);
  const host = normalizeHost(requestHost) || normalizeHost(current.hostname);
  if (!isWwwHost(host)) return null;

  const apex = host.startsWith("www.") ? host.slice(4) : canonicalPublicHost();
  const target = new URL(
    `${current.pathname}${current.search}`,
    `https://${apex || "dxcon.com.vn"}`,
  );
  target.protocol = "https:";
  target.hostname = apex || "dxcon.com.vn";
  target.port = "";
  return target;
}

/**
 * True when host/path/search match after normalization, ignoring protocol/port.
 * Used so proxy http↔https or default-port differences never self-redirect.
 */
export function sameHostPathSearch(left: string | URL, right: string | URL): boolean {
  try {
    const a = left instanceof URL ? left : new URL(left);
    const b = right instanceof URL ? right : new URL(right);
    return (
      normalizeHost(a.hostname) === normalizeHost(b.hostname) &&
      normalizePathname(a.pathname) === normalizePathname(b.pathname) &&
      a.search === b.search
    );
  } catch {
    return false;
  }
}

/**
 * Cross-origin application redirect target for public-site hosts.
 * Returns null when the target would be the same URL or same origin
 * (unified apex deployment where APP_URL === public site).
 *
 * `requestHost` should be the HTTP Host header when available so proxy /
 * local Host-header checks compare the public hostname, not 127.0.0.1.
 */
export function publicSiteAppRedirectTarget(
  requestUrl: string | URL,
  pathname: string,
  search: string,
  appUrl: string = APP_URL,
  requestHost?: string | null,
): URL | null {
  const current = requestUrl instanceof URL ? requestUrl : new URL(requestUrl);
  let target = new URL(`${pathname}${search}`, appUrl);

  // Prefer apex over www so APP_URL mis-set to www cannot fight www→apex.
  if (isWwwHost(target.hostname)) {
    const apex = wwwToApexTarget(target);
    if (apex) target = apex;
  }

  const effectiveHost =
    normalizeHost(requestHost) || normalizeHost(current.hostname);
  const targetHost = normalizeHost(target.hostname);

  if (
    effectiveHost &&
    targetHost &&
    effectiveHost === targetHost &&
    normalizePathname(current.pathname) === normalizePathname(target.pathname) &&
    current.search === target.search
  ) {
    return null;
  }

  if (sameNormalizedUrl(current, target)) return null;
  if (sameHostPathSearch(current, target)) return null;
  if (originOf(current) === originOf(target)) return null;
  return target;
}
