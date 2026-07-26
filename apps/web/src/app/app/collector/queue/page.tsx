"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import {
  fetchCollectionQueue,
  type SampleCollectionItem,
} from "@/lib/api/sampleCollection";
import { normalizeApiError } from "@/lib/errors";

import { DataState, SectionHeader, SimpleTable, StatusPill } from "../_components/ui";

export default function CollectorQueuePage() {
  const { accessToken, activeOrganizationId, can, role } = useAuth();
  const [items, setItems] = useState<SampleCollectionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [location, setLocation] = useState("");
  const [date, setDate] = useState("");
  const [collector, setCollector] = useState("");

  const canRead =
    can("collections.read") ||
    ["COLLECTOR", "PARTNER_COLLECTOR", "DRIVER", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN"].includes(
      role ?? "",
    );

  const load = useCallback(async () => {
    if (!accessToken || !canRead) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCollectionQueue(
        { token: accessToken, organizationId: activeOrganizationId },
        {
          status: status || undefined,
          location: location || undefined,
          date: date || undefined,
          collector: collector || undefined,
          include_desk: true,
        },
      );
      setItems(data.items ?? []);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeOrganizationId, canRead, status, location, date, collector]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <AppShell title="Collection queue" workspacePath="/app/collector">
      <div className="space-y-6">
        <SectionHeader
          title="Specimens awaiting collection"
          description="Filter by location, date, status, and collector. Field and desk jobs are tenant-scoped."
          actions={
            <Button size="sm" variant="outline" onClick={() => void load()}>
              Refresh
            </Button>
          }
        />

        <div className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Status</span>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">Awaiting (default)</option>
              <option value="PENDING">PENDING</option>
              <option value="CHECKED_IN">CHECKED_IN</option>
              <option value="RECOLLECT_REQUIRED">RECOLLECT_REQUIRED</option>
              <option value="COLLECTED">COLLECTED</option>
              <option value="IN_TRANSIT">IN_TRANSIT</option>
              <option value="RECEIVED">RECEIVED</option>
              <option value="REJECTED">REJECTED</option>
            </select>
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Location</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="City or address"
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Date</span>
            <input
              type="date"
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={date}
              onChange={(e) => setDate(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            <span className="mb-1 block text-slate-600">Collector ID</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={collector}
              onChange={(e) => setCollector(e.target.value)}
              placeholder="Optional"
            />
          </label>
        </div>

        {!canRead ? (
          <p className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            You do not have permission to view the collection queue.
          </p>
        ) : (
          <DataState
            loading={loading}
            error={error}
            empty={!loading && items.length === 0}
            emptyLabel="No specimens match these filters."
            onRetry={() => void load()}
          >
            <SimpleTable
              rows={items}
              rowKey={(row) => row.id}
              columns={[
                {
                  key: "patient",
                  label: "Patient / order",
                  render: (row) => (
                    <div>
                      <div className="font-medium">
                        {row.booking?.patient_name ||
                          String((row.order as { patient_name?: string } | null)?.patient_name ?? "—")}
                      </div>
                      <div className="text-xs text-slate-500">
                        {row.booking?.booking_code || row.sample_code || row.id.slice(0, 8)}
                      </div>
                    </div>
                  ),
                },
                {
                  key: "location",
                  label: "Location",
                  render: (row) =>
                    row.location_city ||
                    row.collection_location ||
                    row.pickup_address ||
                    row.booking?.city ||
                    "—",
                },
                {
                  key: "collector",
                  label: "Collector",
                  render: (row) => row.collector_name || row.collector_id || "—",
                },
                {
                  key: "status",
                  label: "Status",
                  render: (row) => <StatusPill status={row.status} />,
                },
                {
                  key: "source",
                  label: "Source",
                  render: (row) => row.source || "field",
                },
                {
                  key: "action",
                  label: "",
                  render: (row) =>
                    row.source === "desk" ? (
                      <span className="text-xs text-slate-400">Desk / reception</span>
                    ) : (
                      <Link
                        href={`/app/collector/workflow?id=${encodeURIComponent(row.id)}`}
                        className="text-sm font-medium text-sky-700 hover:underline"
                      >
                        Open
                      </Link>
                    ),
                },
              ]}
            />
          </DataState>
        )}
      </div>
    </AppShell>
  );
}
