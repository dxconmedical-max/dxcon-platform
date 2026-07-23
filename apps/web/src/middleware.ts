import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { APP_URL, AUTH_COOKIE, ROLE_COOKIE } from "@/lib/constants";
import { isPublicSiteHost, normalizeHost } from "@/lib/domains";
import { parseCookieValue } from "@/lib/cookies";
import {
  publicSiteAppRedirectTarget,
  normalizePathname,
  sameHostPathSearch,
  sameNormalizedUrl,
  wwwToApexTarget,
} from "@/lib/redirects";
import { WORKSPACE_ROUTES, workspacePathForRole } from "@/lib/roles";
import { loginUrl, safeRedirectPath } from "@/lib/urls";

const LEGACY_REDIRECTS: Record<string, string> = {
  "/admin": "/app/admin",
  "/doctor": "/app/doctor",
  "/patient": "/app/patient",
  "/lab": "/app/lab",
  "/collector": "/app/collector",
  "/clinic": "/app/clinic",
};

const KNOWN_APP_PREFIXES = [
  "/app",
  "/login",
  "/register",
  "/logout",
  "/forgot-password",
  "/reset-password",
  "/select-organization",
  "/session-expired",
  "/forbidden",
  "/service-unavailable",
  "/marketplace",
  "/onboarding",
];

function isApplicationPath(pathname: string): boolean {
  return KNOWN_APP_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

function isKnownWorkspacePath(pathname: string): boolean {
  return WORKSPACE_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );
}

/** Never issue a redirect when destination equals the current request URL. */
function redirectUnlessSame(
  request: NextRequest,
  destination: URL,
  status?: number,
): NextResponse | null {
  const host = normalizeHost(request.headers.get("host"));
  const currentPath = normalizePathname(request.nextUrl.pathname);
  const destPath = normalizePathname(destination.pathname);
  const samePublicHostPath =
    Boolean(host) &&
    host === normalizeHost(destination.hostname) &&
    currentPath === destPath &&
    request.nextUrl.search === destination.search;

  if (
    samePublicHostPath ||
    sameNormalizedUrl(request.url, destination) ||
    sameHostPathSearch(request.url, destination)
  ) {
    return null;
  }
  return status === undefined
    ? NextResponse.redirect(destination)
    : NextResponse.redirect(destination, status);
}

export function middleware(request: NextRequest) {
  const host = normalizeHost(request.headers.get("host"));
  const { pathname, search } = request.nextUrl;

  // One-way www → apex (308). Never reverse apex → www.
  const apexTarget = wwwToApexTarget(request.url, host);
  if (apexTarget) {
    const redirected = redirectUnlessSame(request, apexTarget, 308);
    if (redirected) return redirected;
  }

  // Only bounce public-site application routes to APP_URL when the target
  // origin is genuinely different (split-domain deployments). Never redirect
  // when APP_URL shares the current host/path (unified apex).
  if (isPublicSiteHost(host) && isApplicationPath(pathname)) {
    const target = publicSiteAppRedirectTarget(
      request.url,
      pathname,
      search,
      APP_URL,
      host,
    );
    if (target) {
      const redirected = redirectUnlessSame(request, target);
      if (redirected) return redirected;
    }
  }

  if (LEGACY_REDIRECTS[pathname]) {
    const target = new URL(LEGACY_REDIRECTS[pathname], request.url);
    const redirected = redirectUnlessSame(request, target);
    if (redirected) return redirected;
  }

  const cookieHeader = request.headers.get("cookie") ?? undefined;
  const isAuthenticated = parseCookieValue(cookieHeader, AUTH_COOKIE) === "1";
  const role = parseCookieValue(cookieHeader, ROLE_COOKIE);

  if (pathname === "/login" && isAuthenticated) {
    const next = safeRedirectPath(
      request.nextUrl.searchParams.get("next"),
      workspacePathForRole(role),
    );
    const target = new URL(next, request.url);
    const redirected = redirectUnlessSame(request, target);
    if (redirected) return redirected;
  }

  const isProtected = WORKSPACE_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );

  if (isProtected && !isAuthenticated) {
    const login = new URL(loginUrl(host), request.url);
    login.searchParams.set("next", pathname);
    const redirected = redirectUnlessSame(request, login);
    if (redirected) return redirected;
  }

  if (
    isProtected &&
    isAuthenticated &&
    pathname.startsWith("/app/") &&
    !isKnownWorkspacePath(pathname)
  ) {
    return NextResponse.rewrite(new URL("/app/not-found", request.url));
  }

  if (pathname === "/select-organization" && !isAuthenticated) {
    const target = new URL(loginUrl(host), request.url);
    const redirected = redirectUnlessSame(request, target);
    if (redirected) return redirected;
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
