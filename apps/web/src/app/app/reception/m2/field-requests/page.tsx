"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest } from "@/services/api";
import { normalizeApiError } from "@/lib/errors";
import type { SampleCollectionItem } from "@/lib/api/sampleCollection";

import { DataState, SectionHeader, SimpleTable } from "../../_components/ui";

function StatusPill({ status }: { status: string }) {
  return (
    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
      {status}
    </span>
  );
}

type FieldQueue = { count: number; items: SampleCollectionItem[] };

export default function FieldCollectionRequestsPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const [items, setItems] = useState<SampleCollectionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const body = await apiRequest<{ success: boolean; data: FieldQueue }>(
        "/api/v1/reception/workspace/field-collection-requests",
        { method: "GET", token: accessToken, organizationId: activeOrganizationId },
      );
      setItems(body.data?.items ?? []);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeOrganizationId]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <AppShell title="Field collection requests" workspacePath="/app/reception">
      <div className="space-y-6">
        <SectionHeader
          title="HOME / CLINIC collection requests"
          description="Field jobs for dispatcher/collector assignment. Desk AT_RECEPTION work is on Desk collections."
          actions={
            <div className="flex gap-2">
              <Link href="/app/collector/queue" className="text-sm font-medium text-sky-700 hover:underline self-center">
                Open collector queue
              </Link>
              <Button size="sm" variant="outline" onClick={() => void load()}>
                Refresh
              </Button>
            </div>
          }
        />
        <DataState
          loading={loading}
          error={error}
          empty={!loading && items.length === 0}
          emptyLabel="No field collection requests."
          onRetry={() => void load()}
        >
          <SimpleTable
            rows={items}
            rowKey={(row) => row.id}
            columns={[
              {
                key: "patient",
                label: "Patient / order",
                render: (row) =>
                  row.booking?.patient_name ||
                  String((row.order as { patient_name?: string } | null)?.patient_name ?? "—"),
              },
              {
                key: "mode",
                label: "Mode",
                render: (row) => String(row.collection_mode || "—"),
              },
              {
                key: "pickup",
                label: "Pickup",
                render: (row) =>
                  row.pickup_address ||
                  row.collection_location ||
                  row.booking?.patient_address ||
                  "—",
              },
              {
                key: "schedule",
                label: "Schedule",
                render: (row) =>
                  [row.requested_date, row.requested_time_window].filter(Boolean).join(" ") || "—",
              },
              {
                key: "status",
                label: "Status",
                render: (row) => <StatusPill status={row.status} />,
              },
            ]}
          />
        </DataState>
      </div>
    </AppShell>
  );
}
