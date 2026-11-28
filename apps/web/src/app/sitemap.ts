import type { MetadataRoute } from "next";

const BASE = "https://dxcon.com.vn";
const PATHS = ["/vi", "/en", "/vi/about", "/en/about", "/vi/contact", "/vi/faq", "/vi/privacy", "/vi/terms", "/book"];

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return PATHS.map((p) => ({ url: `${BASE}${p}`, lastModified: now, priority: p === "/vi" ? 1 : 0.6 }));
}
