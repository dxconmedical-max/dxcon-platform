import { apiRequest } from "./client";

export type HealthPayload = {
  status?: string;
  service?: string;
  database?: string;
};

export async function fetchHealth(): Promise<HealthPayload> {
  return apiRequest<HealthPayload>("/health");
}

export async function fetchReady(): Promise<HealthPayload> {
  return apiRequest<HealthPayload>("/ready");
}
