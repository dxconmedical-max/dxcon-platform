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
          title="Field collection requests"
          description="HOME and CLINIC requests from Reception. Home jobs also appear on the Collector Queue; CLINIC stays on this board only."
          actions={
            <div className="flex gap-2">
              <Link
                href="/app/collector/queue"
                className="self-center text-sm font-medium text-sky-700 hover:underline"
              >
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
                label: "Patient",
                render: (row) =>
                  row.booking?.patient_name ||
                  String((row.order as { patient_name?: string } | null)?.patient_name ?? "—"),
              },
              {
                key: "order",
                label: "Order",
                render: (row) =>
                  row.booking?.booking_code ||
                  String((row.order as { order_code?: string } | null)?.order_code ?? "—"),
              },
              {
                key: "address",
                label: "Address",
                render: (row) =>
                  row.pickup_address ||
                  row.clinic_name ||
                  row.collection_location ||
                  row.booking?.patient_address ||
                  "—",
              },
              {
                key: "date",
                label: "Requested date",
                render: (row) => row.requested_date || "—",
              },
              {
                key: "time",
                label: "Requested time",
                render: (row) => row.requested_time_window || "—",
              },
              {
                key: "priority",
                label: "Priority",
                render: (row) => String(row.priority || "ROUTINE"),
              },
              {
                key: "status",
                label: "Status",
                render: (row) => <StatusPill status={row.status} />,
              },
              {
                key: "collector",
                label: "Assigned collector",
                render: (row) => row.collector_name || "—",
              },
              {
                key: "actions",
                label: "Actions",
                render: (row) => (
                  <Link
                    href="/app/collector/queue"
                    className="text-sm font-medium text-sky-700 hover:underline"
                  >
                    {row.status === "PENDING_ASSIGNMENT" ? "Assign" : "View"}
                  </Link>
                ),
              },
            ]}
          />
        </DataState>
      </div>
    </AppShell>
  );
}
