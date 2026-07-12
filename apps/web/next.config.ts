import type { NextConfig } from "next";

const isProduction =
  (process.env.NEXT_PUBLIC_APP_ENV ?? "development") === "production";

const required = [
  "NEXT_PUBLIC_API_BASE_URL",
  "NEXT_PUBLIC_PUBLIC_SITE_URL",
  "NEXT_PUBLIC_APP_URL",
  "NEXT_PUBLIC_APP_ENV",
];

if (isProduction) {
  const missing = required.filter((key) => !process.env[key]);
  if ((process.env.NEXT_PUBLIC_DEMO_MODE ?? "false").toLowerCase() === "true") {
    missing.push("NEXT_PUBLIC_DEMO_MODE must be false in production");
  }
  if (missing.length > 0) {
    throw new Error(
      `Missing required production environment variables: ${missing.join(", ")}`,
    );
  }
}

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "https://api.dxcon.com.vn";

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=()",
  },
  { key: "X-Frame-Options", value: "DENY" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https:",
      `connect-src 'self' ${apiBaseUrl}`,
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "form-action 'self'",
    ].join("; "),
  },
];

const nextConfig: NextConfig = {
  async headers() {
    return [
      { source: "/(.*)", headers: securityHeaders },
      {
        source: "/app/:path*",
        headers: [{ key: "Cache-Control", value: "private, no-store, max-age=0" }],
      },
    ];
  },
};

export default nextConfig;
