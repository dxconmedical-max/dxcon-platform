export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(message: string, status: number, body: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export function isRequestAborted(error: unknown): boolean {
  return (
    error instanceof ApiError &&
    (error.status === 499 ||
      (typeof error.body === "object" &&
        error.body != null &&
        (error.body as { code?: string }).code === "ABORTED"))
  );
}

/**
 * Extract a human-readable message from API error payloads.
 * Handles string errors and envelope objects `{ code, message }` —
 * never returns "[object Object]".
 */
export function extractApiErrorMessage(value: unknown): string | null {
  if (value == null) return null;
  if (typeof value === "string") {
    const trimmed = value.trim();
    return trimmed && trimmed !== "[object Object]" ? trimmed : null;
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    for (const key of ["message", "detail", "title"] as const) {
      const nested = record[key];
      if (typeof nested === "string" && nested.trim()) {
        return nested.trim();
      }
    }
    // Nested envelope: { error: { message } } or { error: "text" }
    if ("error" in record) {
      const nested = extractApiErrorMessage(record.error);
      if (nested) return nested;
    }
    if (typeof record.code === "string" && record.code.trim()) {
      return record.code.trim();
    }
  }
  return null;
}

export function normalizeApiError(error: unknown): string {
  if (error instanceof ApiError) {
    if (isRequestAborted(error)) {
      return "Request cancelled.";
    }
    if (error.status === 429) {
      return "Too many attempts. Please wait and try again.";
    }
    if (error.status === 408) {
      return error.message || "Request timed out. Please try again.";
    }
    // Never treat HTTP 4xx/5xx as a generic network failure.
    if (error.status === 0) {
      return "Network error — check your connection.";
    }
    if (typeof error.body === "object" && error.body && "error" in error.body) {
      const fromBody = extractApiErrorMessage(
        (error.body as { error: unknown }).error,
      );
      if (fromBody) return fromBody;
    }
    const fromMessage = extractApiErrorMessage(error.message);
    if (fromMessage) return fromMessage;
    if (error.status === 403) {
      return "You do not have permission for this action.";
    }
    if (error.status === 401) {
      return "Authentication required.";
    }
    return `Request failed (${error.status})`;
  }
  if (error instanceof Error) {
    return extractApiErrorMessage(error.message) || "An unexpected error occurred";
  }
  return extractApiErrorMessage(error) || "An unexpected error occurred";
}

export function loginErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return normalizeApiError(error);
  }
  switch (error.status) {
    case 400:
      return (
        (typeof error.body === "object" &&
          error.body &&
          "error" in error.body &&
          extractApiErrorMessage((error.body as { error: unknown }).error)) ||
        extractApiErrorMessage(error.message) ||
        "Invalid login request."
      );
    case 401:
      return "Invalid email or password.";
    case 403:
      return "This account has been disabled.";
    case 429:
      return "Too many login attempts. Please wait and try again.";
    case 0:
      return "Network error — check your connection and try again.";
    case 408:
      return "Sign-in timed out. Please try again.";
    case 502:
      if (
        typeof error.body === "object" &&
        error.body &&
        (error.body as { code?: string }).code === "MALFORMED_LOGIN_RESPONSE"
      ) {
        return "Unexpected login response from server. Please try again.";
      }
      return extractApiErrorMessage(error.message) || "Service temporarily unavailable.";
    default:
      // Preserve real backend messages for 500 and other statuses.
      return (
        extractApiErrorMessage(error.message) || `Request failed (${error.status})`
      );
  }
}
