import { IS_PRODUCTION, PUBLIC_SITE_URL, APP_URL } from "@/lib/constants";

export const PUBLIC_SITE_HOSTS = ["dxcon.com.vn", "www.dxcon.com.vn"] as const;
export const APP_HOSTS = ["app.dxcon.com.vn"] as const;

export type HostKind = "public_site" | "application" | "preview";

export function normalizeHost(host: string | null | undefined): string {
  if (!host) return "";
  return host.split(":")[0].toLowerCase();
}

export function hostFromUrl(url: string): string {
  try {
    return normalizeHost(new URL(url).hostname);
  } catch {
    return "";
  }
}

export function isPublicSiteHost(host: string | null | undefined): boolean {
  const normalized = normalizeHost(host);
  if (PUBLIC_SITE_HOSTS.includes(normalized as (typeof PUBLIC_SITE_HOSTS)[number])) {
    return true;
  }
  return IS_PRODUCTION && normalized === hostFromUrl(PUBLIC_SITE_URL);
}

export function isAppHost(host: string | null | undefined): boolean {
  const normalized = normalizeHost(host);
  if (APP_HOSTS.includes(normalized as (typeof APP_HOSTS)[number])) {
    return true;
  }
  return IS_PRODUCTION && normalized === hostFromUrl(APP_URL);
}

export function hostKind(host: string | null | undefined): HostKind {
  if (isAppHost(host)) return "application";
  if (isPublicSiteHost(host)) return "public_site";
  return "preview";
}

export function isPreviewHost(host: string | null | undefined): boolean {
  return hostKind(host) === "preview";
}
