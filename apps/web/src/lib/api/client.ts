import { API_BASE_URL, API_TIMEOUT_MS } from "@/lib/constants";
import { ApiError, mapResponseToApiError } from "@/lib/errors";

export type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
  refreshToken?: string | null;
  organizationId?: string | null;
  headers?: Record<string, string>;
  correlationId?: string;
  idempotencyKey?: string;
  timeoutMs?: number;
  signal?: AbortSignal;
};

function generateCorrelationId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `dxcon-${Date.now()}`;
}

function generateIdempotencyKey(): string {
  return generateCorrelationId();
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    method = "GET",
    body,
    token,
    refreshToken,
    organizationId,
    headers = {},
    correlationId = generateCorrelationId(),
    idempotencyKey,
    timeoutMs = API_TIMEOUT_MS,
    signal,
  } = options;

  const requestHeaders: Record<string, string> = {
    Accept: "application/json",
    "X-Correlation-ID": correlationId,
    ...headers,
  };

  if (body !== undefined) {
    requestHeaders["Content-Type"] = "application/json";
  }

  const bearer = refreshToken ?? token;
  if (bearer) {
    requestHeaders.Authorization = `Bearer ${bearer}`;
  }
  if (organizationId) {
    requestHeaders["X-Organization-ID"] = organizationId;
  }
  if (idempotencyKey ?? (method !== "GET" && method !== "HEAD")) {
    requestHeaders["Idempotency-Key"] =
      idempotencyKey ?? generateIdempotencyKey();
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  if (signal) {
    signal.addEventListener("abort", () => controller.abort(), { once: true });
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: requestHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      cache: "no-store",
      signal: controller.signal,
    });
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new ApiError({
        code: "TIMEOUT",
        message: "Request timed out",
        status: 408,
        correlationId,
        retryable: true,
      });
    }
    throw new ApiError({
      code: "NETWORK_ERROR",
      message: "Network error — check your connection",
      status: 0,
      correlationId,
      retryable: true,
    });
  } finally {
    clearTimeout(timer);
  }

  const responseCorrelationId =
    response.headers.get("X-Correlation-ID") ?? correlationId;
  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    throw mapResponseToApiError(response.status, payload, responseCorrelationId);
  }

  return payload as T;
}

export type ApiEnvelope<T> = { success: boolean; data: T };
