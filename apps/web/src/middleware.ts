import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { APP_URL } from "@/lib/constants";
import { isPublicSiteHost, normalizeHost } from "@/lib/domains";
import { parseCookieValue } from "@/lib/cookies";
import { WORKSPACE_ROUTES, workspacePathForRole } from "@/lib/roles";
import { loginUrl, safeRedirectPath } from "@/lib/urls";

const AUTH_COOKIE = "dxcon_authenticated";

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

export function middleware(request: NextRequest) {
  const host = normalizeHost(request.headers.get("host"));
  const { pathname, search } = request.nextUrl;

  if (host === "www.dxcon.com.vn") {
    const apex = request.nextUrl.clone();
    apex.hostname = "dxcon.com.vn";
    return NextResponse.redirect(apex, 308);
  }

  if (isPublicSiteHost(host) && isApplicationPath(pathname)) {
    const target = new URL(`${pathname}${search}`, APP_URL);
    return NextResponse.redirect(target);
  }

  if (LEGACY_REDIRECTS[pathname]) {
    return NextResponse.redirect(
      new URL(LEGACY_REDIRECTS[pathname], request.url),
    );
  }

  const cookieHeader = request.headers.get("cookie") ?? undefined;
  const isAuthenticated = parseCookieValue(cookieHeader, AUTH_COOKIE) === "1";
  const role = parseCookieValue(cookieHeader, "dxcon_role");

  if (pathname === "/login" && isAuthenticated) {
    const next = safeRedirectPath(
      request.nextUrl.searchParams.get("next"),
      workspacePathForRole(role),
    );
    return NextResponse.redirect(new URL(next, request.url));
  }

  const isProtected = WORKSPACE_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );

  if (isProtected && !isAuthenticated) {
    const login = new URL(loginUrl(host), request.url);
    login.searchParams.set("next", pathname);
    return NextResponse.redirect(login);
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
    return NextResponse.redirect(new URL(loginUrl(host), request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
