export type ApiErrorShape = {
  code: string;
  message: string;
  status: number;
  correlationId?: string;
  fieldErrors?: Record<string, string[]>;
  retryable: boolean;
};

export class ApiError extends Error implements ApiErrorShape {
  code: string;
  status: number;
  correlationId?: string;
  fieldErrors?: Record<string, string[]>;
  retryable: boolean;
  body: unknown;

  constructor(shape: ApiErrorShape & { body?: unknown }) {
    super(shape.message);
    this.name = "ApiError";
    this.code = shape.code;
    this.status = shape.status;
    this.correlationId = shape.correlationId;
    this.fieldErrors = shape.fieldErrors;
    this.retryable = shape.retryable;
    this.body = shape.body ?? null;
  }
}

function retryableForStatus(status: number): boolean {
  return status === 0 || status === 408 || status === 429 || status >= 500;
}

export function mapResponseToApiError(
  status: number,
  payload: unknown,
  correlationId?: string,
): ApiError {
  const body =
    typeof payload === "object" && payload !== null
      ? (payload as Record<string, unknown>)
      : {};

  const nestedError =
    body.error && typeof body.error === "object"
      ? (body.error as Record<string, unknown>)
      : null;
  const nestedData =
    body.data && typeof body.data === "object"
      ? (body.data as Record<string, unknown>)
      : null;

  const code = String(
    nestedError?.code ??
      body.code ??
      nestedData?.code ??
      defaultCodeForStatus(status),
  );

  const rawMessage =
    nestedError?.message ??
    (typeof body.error === "string" ? body.error : null) ??
    body.message ??
    nestedData?.error ??
    nestedData?.message ??
    null;

  const message = String(rawMessage ?? defaultMessageForStatus(status));
  const fieldErrors = extractFieldErrors(
    nestedError ?? nestedData ?? body,
  );

  return new ApiError({
    code,
    message,
    status,
    correlationId,
    fieldErrors,
    retryable: retryableForStatus(status),
    body: payload,
  });
}

function defaultCodeForStatus(status: number): string {
  switch (status) {
    case 401:
      return "UNAUTHORIZED";
    case 403:
      return "FORBIDDEN";
    case 404:
      return "NOT_FOUND";
    case 409:
      return "CONFLICT";
    case 422:
      return "VALIDATION_ERROR";
    case 429:
      return "RATE_LIMITED";
    default:
      return status >= 500 ? "SERVER_ERROR" : "REQUEST_FAILED";
  }
}

function defaultMessageForStatus(status: number): string {
  switch (status) {
    case 401:
      return "Authentication required";
    case 403:
      return "You do not have permission to perform this action";
    case 404:
      return "The requested resource was not found";
    case 409:
      return "This action conflicts with existing data";
    case 422:
      return "Validation failed";
    case 429:
      return "Too many requests. Please wait and try again.";
    default:
      return status >= 500
        ? "Service temporarily unavailable"
        : `Request failed (${status})`;
  }
}

function extractFieldErrors(
  body: Record<string, unknown>,
): Record<string, string[]> | undefined {
  if (body.field_errors && typeof body.field_errors === "object") {
    return body.field_errors as Record<string, string[]>;
  }
  if (body.errors && typeof body.errors === "object") {
    return body.errors as Record<string, string[]>;
  }
  return undefined;
}

export function normalizeApiError(error: unknown): string {
  if (error instanceof ApiError) {
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
      if (error.code === "ORGANIZATION_SUSPENDED") {
        return "Your organization is suspended. Contact your administrator.";
      }
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
