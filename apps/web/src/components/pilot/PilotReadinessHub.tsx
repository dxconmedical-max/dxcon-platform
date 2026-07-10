"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { API_BASE_URL } from "@/lib/constants";
import { useAuthStore } from "@/stores/authStore";

type HubProps = {
  title: string;
  subtitle: string;
  endpoint: string;
  requiresAuth?: boolean;
};

export function PilotReadinessHub({
  title,
  subtitle,
  endpoint,
  requiresAuth = true,
}: HubProps) {
  const token = useAuthStore((s) => s.accessToken);
  const organizationId = useAuthStore((s) => s.activeOrganizationId);
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (requiresAuth && token) {
      headers.Authorization = `Bearer ${token}`;
    }
    if (organizationId) {
      headers["X-Organization-ID"] = organizationId;
    }
    fetch(`${API_BASE_URL}${endpoint}`, { headers })
      .then(async (res) => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const json = await res.json();
        setData(json.data ?? json);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [endpoint, token, organizationId, requiresAuth]);

  const widgets =
    (data?.widgets as Record<string, unknown>) ??
    (data?.components as Array<{ component: string; status: string }>) ??
    null;

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-teal-50/40 p-6">
        <Badge tone="info">Epic 8 — Production readiness</Badge>
        <h2 className="mt-3 text-2xl font-semibold text-slate-900">{title}</h2>
        <p className="mt-2 text-slate-600">{subtitle}</p>
      </section>

      {loading ? <p className="text-slate-500">Loading…</p> : null}
      {error ? (
        <Card>
          <CardTitle>Unable to load live data</CardTitle>
          <CardDescription>
            {error}. Sign in with an authorized role or verify API connectivity.
          </CardDescription>
        </Card>
      ) : null}

      {widgets && !Array.isArray(widgets) ? (
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {Object.entries(widgets).map(([key, value]) => (
            <Card key={key}>
              <p className="text-sm text-slate-500">{key.replace(/_/g, " ")}</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{String(value)}</p>
            </Card>
          ))}
        </section>
      ) : null}

      {Array.isArray(widgets) ? (
        <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {widgets.map((item) => (
            <Card key={item.component}>
              <p className="text-sm text-slate-500">{item.component}</p>
              <p className="mt-2 text-xl font-semibold text-slate-900">{item.status}</p>
            </Card>
          ))}
        </section>
      ) : null}

      {typeof data?.production_score === "number" ? (
        <Card>
          <CardTitle>Production readiness score</CardTitle>
          <p className="mt-2 text-3xl font-semibold text-teal-700">
            {data.production_score}/100
          </p>
        </Card>
      ) : null}
    </div>
  );
}
