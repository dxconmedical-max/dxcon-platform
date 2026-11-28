import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: "*", allow: "/", disallow: ["/app/", "/api/", "/r/", "/login", "/logout", "/reset-password", "/forgot-password", "/select-organization", "/onboarding"] }],
    sitemap: "https://dxcon.com.vn/sitemap.xml",
  };
}
