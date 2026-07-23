import { API_BASE_URL, API_TIMEOUT_MS } from "@/lib/constants";
import { ApiError } from "@/lib/errors";

export type RequestOptions = {
  method?: string;
  body?: unknown;
  token?: string | null;
  refreshToken?: string | null;
  organizationId?: string | null;
  headers?: Record<string, string>;
  correlationId?: string;
  timeoutMs?: number;
  /** Optional caller abort (e.g. debounce cancel). Distinct from timeout. */
  signal?: AbortSignal;
};

function generateCorrelationId(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `dxcon-${Date.now()}`;
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

  const controller = new AbortController();
  const onExternalAbort = () => {
    controller.abort();
  };
  if (signal) {
    if (signal.aborted) {
      throw new ApiError("Request cancelled", 499, { code: "ABORTED" });
    }
    signal.addEventListener("abort", onExternalAbort, { once: true });
  }
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let response: Response;
  try {
    console.debug("[apiRequest] fetch", { method, path });
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      headers: requestHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      cache: "no-store",
      signal: controller.signal,
    });
    console.debug("[apiRequest] response", { status: response.status, path });
  } catch (error) {
    console.debug("[apiRequest] fetch failed", { path, name: (error as Error)?.name });
    if (error instanceof Error && error.name === "AbortError") {
      if (signal?.aborted) {
        throw new ApiError("Request cancelled", 499, { code: "ABORTED" });
      }
      throw new ApiError("Request timed out", 408, { code: "TIMEOUT" });
    }
    throw new ApiError("Network error — check your connection", 0, {
      code: "NETWORK_ERROR",
    });
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", onExternalAbort);
  }

  const contentType = response.headers.get("content-type") ?? "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const code =
      typeof payload === "object" && payload && "code" in payload
        ? String((payload as { code: unknown }).code)
        : undefined;
    const message =
      typeof payload === "object" && payload && "error" in payload
        ? String((payload as { error: unknown }).error)
        : `Request failed (${response.status})`;
    throw new ApiError(message, response.status, { ...((payload as object) || {}), code });
  }

  return payload as T;
}

export async function healthCheck(): Promise<{ status?: string }> {
  return apiRequest("/health");
}
