/**
 * Returns a safe relative path for post-login redirects.
 * Rejects absolute URLs and protocol-relative paths.
 */
export function safeRedirectPath(
  next: string | null | undefined,
  fallback = "/app",
): string {
  if (!next) return fallback;
  if (!next.startsWith("/") || next.startsWith("//")) return fallback;
  if (next.includes("://")) return fallback;
  return next;
}
