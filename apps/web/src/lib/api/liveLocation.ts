import { apiRequest } from "@/services/api";

export type LiveCollector = {
  user_id: string;
  email: string;
  latitude: number;
  longitude: number;
  accuracy_m?: number | null;
  heading?: number | null;
  speed_kmh?: number | null;
  recorded_at: string;
};

type Ctx = { token: string | null; organizationId: string | null };

export type PingInput = {
  latitude: number;
  longitude: number;
  accuracy_m?: number;
  heading?: number;
  speed_kmh?: number;
};

export async function sendPing(ctx: Ctx, body: PingInput): Promise<void> {
  await apiRequest("/api/v1/live-location/ping", {
    method: "POST",
    body,
    token: ctx.token,
    organizationId: ctx.organizationId,
  });
}

export async function stopSharing(ctx: Ctx): Promise<void> {
  await apiRequest("/api/v1/live-location/ping", {
    method: "DELETE",
    token: ctx.token,
    organizationId: ctx.organizationId,
  });
}

export async function fetchCollectors(ctx: Ctx): Promise<LiveCollector[]> {
  const res = await apiRequest<{
    collectors?: LiveCollector[];
    data?: { collectors?: LiveCollector[] };
  }>("/api/v1/live-location/collectors", {
    token: ctx.token,
    organizationId: ctx.organizationId,
  });
  return res.collectors ?? res.data?.collectors ?? [];
}

export function googleMapsUrl(latitude: number, longitude: number): string {
  return `https://www.google.com/maps?q=${latitude},${longitude}`;
}
