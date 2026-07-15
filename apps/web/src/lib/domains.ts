import { APP_ENV, APP_URL, IS_PRODUCTION, PUBLIC_SITE_URL } from "@/lib/constants";

/** Production marketing hosts */
export const PUBLIC_SITE_HOSTS = [
  "dxcon.com.vn",
  "www.dxcon.com.vn",
  "staging.dxcon.com.vn",
] as const;

/** Production / staging application hosts */
export const APP_HOSTS = ["app.dxcon.com.vn", "app-staging.dxcon.com.vn"] as const;

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

function isDeployedSplitEnv(): boolean {
  return IS_PRODUCTION || APP_ENV === "staging";
}

export function isPublicSiteHost(host: string | null | undefined): boolean {
  const normalized = normalizeHost(host);
  if (PUBLIC_SITE_HOSTS.includes(normalized as (typeof PUBLIC_SITE_HOSTS)[number])) {
    return true;
  }
  if (isDeployedSplitEnv() && normalized === hostFromUrl(PUBLIC_SITE_URL)) {
    return true;
  }
  return false;
}

export function isAppHost(host: string | null | undefined): boolean {
  const normalized = normalizeHost(host);
  if (APP_HOSTS.includes(normalized as (typeof APP_HOSTS)[number])) {
    return true;
  }
  if (isDeployedSplitEnv() && normalized === hostFromUrl(APP_URL)) {
    return true;
  }
  return false;
}

export function hostKind(host: string | null | undefined): HostKind {
  if (isAppHost(host)) return "application";
  if (isPublicSiteHost(host)) return "public_site";
  return "preview";
}

export function isPreviewHost(host: string | null | undefined): boolean {
  return hostKind(host) === "preview";
}
