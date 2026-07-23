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

export function normalizeApiError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 429) {
      return "Too many attempts. Please wait and try again.";
    }
    if (error.status === 0) {
      return "Network error — check your connection.";
    }
    if (typeof error.body === "object" && error.body && "error" in error.body) {
      return String((error.body as { error: unknown }).error);
    }
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected error occurred";
}

export function loginErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return normalizeApiError(error);
  }
  switch (error.status) {
    case 401:
      return "Invalid email or password.";
    case 403:
      return "This account has been disabled.";
    case 429:
      return "Too many login attempts. Please wait and try again.";
    case 0:
    case 408:
      return "Network error — check your connection and try again.";
    default:
      return error.message;
  }
}
