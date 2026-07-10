import { AUTH_COOKIE, ORG_COOKIE, ROLE_COOKIE } from "@/lib/constants";

const MAX_AGE_DAYS = 14;

function maxAgeSeconds(): number {
  return MAX_AGE_DAYS * 24 * 60 * 60;
}

export function setAuthCookies(
  role: string,
  organizationId: string | null,
  remember = false,
): void {
  if (typeof document === "undefined") return;
  const maxAge = remember ? maxAgeSeconds() : "";
  const maxAgePart = maxAge ? `; max-age=${maxAge}` : "";
  const secure = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${AUTH_COOKIE}=1; path=/; SameSite=Lax${maxAgePart}${secure}`;
  document.cookie = `${ROLE_COOKIE}=${encodeURIComponent(role)}; path=/; SameSite=Lax${maxAgePart}${secure}`;
  if (organizationId) {
    document.cookie = `${ORG_COOKIE}=${encodeURIComponent(organizationId)}; path=/; SameSite=Lax${maxAgePart}${secure}`;
  }
}

export function clearAuthCookies(): void {
  if (typeof document === "undefined") return;
  for (const name of [AUTH_COOKIE, ROLE_COOKIE, ORG_COOKIE]) {
    document.cookie = `${name}=; path=/; max-age=0`;
  }
}

export function parseCookieValue(
  cookieHeader: string | undefined,
  name: string,
): string | null {
  if (!cookieHeader) return null;
  const match = cookieHeader
    .split(";")
    .map((part) => part.trim())
    .find((part) => part.startsWith(`${name}=`));
  if (!match) return null;
  return decodeURIComponent(match.slice(name.length + 1));
}
