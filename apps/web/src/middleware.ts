import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { AUTH_COOKIE } from "@/lib/constants";
import { parseCookieValue } from "@/lib/cookies";
import { WORKSPACE_ROUTES } from "@/lib/roles";

const LEGACY_REDIRECTS: Record<string, string> = {
  "/admin": "/app/admin",
  "/doctor": "/app/doctor",
  "/patient": "/app/patient",
  "/lab": "/app/lab",
  "/collector": "/app/collector",
  "/clinic": "/app/clinic",
};

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const cookieHeader = request.headers.get("cookie") ?? undefined;
  const cookieAuthenticated =
    parseCookieValue(cookieHeader, AUTH_COOKIE) === "1";

  if (LEGACY_REDIRECTS[pathname]) {
    return NextResponse.redirect(
      new URL(LEGACY_REDIRECTS[pathname], request.url),
    );
  }

  // Do NOT bounce /login → workspace based on the cookie alone.
  // Client AuthProvider/restoreSession owns authenticated vs anonymous.

  const isProtected = WORKSPACE_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );

  if (isProtected && !cookieAuthenticated) {
    console.info("[auth-bootstrap:middleware]", {
      pathname,
      cookieAuthenticated,
      sessionAuthenticated: null,
      redirectReason: "no_auth_cookie→login",
    });
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (pathname === "/select-organization" && !cookieAuthenticated) {
    console.info("[auth-bootstrap:middleware]", {
      pathname,
      cookieAuthenticated,
      sessionAuthenticated: null,
      redirectReason: "no_auth_cookie→login",
    });
    return NextResponse.redirect(new URL("/login", request.url));
  }

  if (isProtected) {
    console.info("[auth-bootstrap:middleware]", {
      pathname,
      cookieAuthenticated,
      sessionAuthenticated: null,
      redirectReason: "allow_protected_route",
    });
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/login",
    "/select-organization",
    "/admin",
    "/doctor",
    "/patient",
    "/lab",
    "/collector",
    "/clinic",
    "/app",
    "/app/:path*",
  ],
};
