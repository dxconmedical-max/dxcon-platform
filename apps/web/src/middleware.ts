import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { AUTH_COOKIE } from "@/lib/constants";
import { parseCookieValue } from "@/lib/cookies";
import { WORKSPACE_ROUTES, workspacePathForRole } from "@/lib/roles";

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
  const isAuthenticated = parseCookieValue(cookieHeader, AUTH_COOKIE) === "1";
  const role = parseCookieValue(cookieHeader, "dxcon_role");

  if (LEGACY_REDIRECTS[pathname]) {
    return NextResponse.redirect(
      new URL(LEGACY_REDIRECTS[pathname], request.url),
    );
  }

  if (pathname === "/login" && isAuthenticated) {
    return NextResponse.redirect(
      new URL(workspacePathForRole(role), request.url),
    );
  }

  const isProtected = WORKSPACE_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );

  if (isProtected && !isAuthenticated) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (pathname === "/select-organization" && !isAuthenticated) {
    return NextResponse.redirect(new URL("/login", request.url));
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
