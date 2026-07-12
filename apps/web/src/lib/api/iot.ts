import { apiRequest, type ApiEnvelope } from "@/lib/api/client";
import { withSampleFallback, SAMPLE_NOTE, type Sourced } from "@/lib/api/adapter";

type Ctx = { token: string; organizationId: string };

export type IoTTrip = {
  id: string;
  trip_code: string;
  status: string;
  vehicle_id?: string;
  container_id?: string;
  latest_latitude?: number;
  latest_longitude?: number;
};

export type IoTAlert = {
  id: string;
  alert_type: string;
  severity: string;
  status: string;
  message?: string;
  device_id?: string;
  trip_id?: string;
};

export type IoTExcursion = {
  id: string;
  excursion_type: string;
  state: string;
  specimen_hold: boolean;
  device_id?: string;
  trip_id?: string;
};

export type LogisticsDashboard = {
  kpis: {
    active_trips: number;
    open_alerts: number;
    active_excursions: number;
    offline_devices: number;
    delayed_trips: number;
  };
};

export type IoTReading = {
  id: string;
  device_id: string;
  recorded_at: string;
  temperature_c?: number;
  humidity_percent?: number;
  latitude?: number;
  longitude?: number;
  simulated?: boolean;
};

export async function fetchLogisticsDashboard(ctx: Ctx): Promise<Sourced<LogisticsDashboard>> {
  return withSampleFallback<LogisticsDashboard>(
    async () => {
      const res = await apiRequest<ApiEnvelope<LogisticsDashboard>>("/api/v1/logistics/dashboard", {
        token: ctx.token,
        organizationId: ctx.organizationId,
      });
      if (!res.data?.kpis) throw new Error("no dashboard");
      return res.data;
    },
    {
      kpis: { active_trips: 0, open_alerts: 0, active_excursions: 0, offline_devices: 0, delayed_trips: 0 },
    },
    SAMPLE_NOTE,
  );
}

export async function fetchIoTTrips(ctx: Ctx): Promise<Sourced<{ trips: IoTTrip[]; total: number }>> {
  return withSampleFallback(
    async () => {
      const res = await apiRequest<ApiEnvelope<{ trips: IoTTrip[]; total: number }>>("/api/v1/logistics/trips", {
        token: ctx.token,
        organizationId: ctx.organizationId,
      });
      return res.data ?? { trips: [], total: 0 };
    },
    { trips: [], total: 0 },
    SAMPLE_NOTE,
  );
}

export async function fetchIoTAlerts(ctx: Ctx): Promise<Sourced<{ alerts: IoTAlert[]; total: number }>> {
  return withSampleFallback(
    async () => {
      const res = await apiRequest<ApiEnvelope<{ alerts: IoTAlert[]; total: number }>>("/api/v1/iot/alerts", {
        token: ctx.token,
        organizationId: ctx.organizationId,
      });
      return res.data ?? { alerts: [], total: 0 };
    },
    { alerts: [], total: 0 },
    SAMPLE_NOTE,
  );
}

export async function fetchIoTExcursions(ctx: Ctx): Promise<Sourced<{ excursions: IoTExcursion[] }>> {
  return withSampleFallback(
    async () => {
      const res = await apiRequest<ApiEnvelope<{ excursions: IoTExcursion[] }>>("/api/v1/iot/excursions", {
        token: ctx.token,
        organizationId: ctx.organizationId,
      });
      return res.data ?? { excursions: [] };
    },
    { excursions: [] },
    SAMPLE_NOTE,
  );
}

export async function fetchContainerReadings(
  ctx: Ctx,
  deviceId: string,
): Promise<Sourced<{ readings: IoTReading[] }>> {
  return withSampleFallback(
    async () => {
      const res = await apiRequest<ApiEnvelope<{ readings: IoTReading[]; total: number }>>(
        `/api/v1/iot/readings?device_id=${encodeURIComponent(deviceId)}`,
        { token: ctx.token, organizationId: ctx.organizationId },
      );
      return { readings: res.data?.readings ?? [] };
    },
    { readings: [] },
    SAMPLE_NOTE,
  );
}
