"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest } from "@/services/api";
import { normalizeApiError } from "@/lib/errors";
import {
  arriveAtLab,
  collectSpecimen,
  fetchCollection,
  verifyCollection,
  type SampleCollectionItem,
} from "@/lib/api/sampleCollection";

import { DataState, SectionHeader, SimpleTable } from "../_components/ui";

function StatusPill({ status }: { status: string }) {
  return (
    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">
      {status}
    </span>
  );
}

type DeskQueue = { count: number; items: SampleCollectionItem[] };

export default function ReceptionDeskCollectionsPage() {
  const { accessToken, activeOrganizationId, role } = useAuth();
  const [items, setItems] = useState<SampleCollectionItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<SampleCollectionItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [barcode, setBarcode] = useState("");

  const canWrite = ["RECEPTION", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN"].includes(role ?? "");

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const body = await apiRequest<{ success: boolean; data: DeskQueue }>(
        "/api/v1/reception/workspace/desk-collections",
        {
          method: "GET",
          token: accessToken,
          organizationId: activeOrganizationId,
        },
      );
      const rows = body.data?.items ?? [];
      setItems(rows);
      if (selectedId) {
        const row = await fetchCollection(
          { token: accessToken, organizationId: activeOrganizationId },
          selectedId,
        );
        setDetail(row);
        setBarcode(row.expected_barcode || row.barcode_value || "");
      }
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeOrganizationId, selectedId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function openRow(id: string) {
    setSelectedId(id);
    setMessage(null);
    setError(null);
    try {
      const row = await fetchCollection(
        { token: accessToken, organizationId: activeOrganizationId },
        id,
      );
      setDetail(row);
      setBarcode(row.expected_barcode || row.barcode_value || "");
    } catch (err) {
      setError(normalizeApiError(err));
    }
  }

  async function onVerify() {
    if (!selectedId || !canWrite) return;
    setBusy(true);
    setError(null);
    try {
      await verifyCollection(
        { token: accessToken, organizationId: activeOrganizationId },
        selectedId,
        {
          patient_name: detail?.booking?.patient_name,
          booking_code: detail?.booking?.booking_code,
          scanned_barcode: barcode || undefined,
        },
      );
      setMessage("Verified.");
      await openRow(selectedId);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onCollect() {
    if (!selectedId || !canWrite) return;
    setBusy(true);
    setError(null);
    try {
      await collectSpecimen(
        { token: accessToken, organizationId: activeOrganizationId },
        selectedId,
        {
          scanned_barcode: barcode,
          require_barcode: true,
          patient_verified: true,
          order_verified: true,
          collection_location: "Reception Desk",
        },
      );
      setMessage("Specimen collected at reception.");
      await openRow(selectedId);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onLabHandover() {
    if (!selectedId || !canWrite) return;
    setBusy(true);
    setError(null);
    try {
      await arriveAtLab(
        { token: accessToken, organizationId: activeOrganizationId },
        selectedId,
        { note: "Reception desk handover to laboratory" },
      );
      setMessage("Handed over to laboratory.");
      await openRow(selectedId);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="Desk collections" workspacePath="/app/reception">
      <div className="space-y-6">
        <SectionHeader
          title="Reception desk collections"
          description="AT_RECEPTION only — verify, barcode, collect, and hand over to lab. Not field collector jobs."
          actions={
            <Button size="sm" variant="outline" onClick={() => void load()}>
              Refresh
            </Button>
          }
        />
        {error ? <p className="text-sm text-rose-700">{error}</p> : null}
        {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
        <DataState
          loading={loading}
          error={null}
          empty={!loading && items.length === 0}
          emptyLabel="No desk collections awaiting work."
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
                      {row.booking?.patient_name || String((row.order as { patient_name?: string } | null)?.patient_name ?? "—")}
                    </div>
                    <div className="text-xs text-slate-500">
                      {row.booking?.booking_code || row.id.slice(0, 8)}
                    </div>
                  </div>
                ),
              },
              {
                key: "mode",
                label: "Mode",
                render: (row) => String(row.collection_mode || "AT_RECEPTION"),
              },
              {
                key: "status",
                label: "Status",
                render: (row) => <StatusPill status={row.status} />,
              },
              {
                key: "action",
                label: "",
                render: (row) => (
                  <button
                    type="button"
                    className="text-sm font-medium text-sky-700 hover:underline"
                    onClick={() => void openRow(row.id)}
                  >
                    Open
                  </button>
                ),
              },
            ]}
          />
        </DataState>

        {detail ? (
          <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
            <p className="text-sm font-medium text-slate-900">
              Desk workflow · {detail.booking?.booking_code || detail.id.slice(0, 8)} · {detail.status}
            </p>
            <label className="block text-sm">
              <span className="mb-1 block text-slate-600">Barcode</span>
              <input
                className="w-full rounded-lg border border-slate-300 px-3 py-2"
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
              />
            </label>
            <div className="flex flex-wrap gap-2">
              <Button size="sm" disabled={busy || !canWrite} onClick={() => void onVerify()}>
                Verify
              </Button>
              <Button size="sm" disabled={busy || !canWrite} onClick={() => void onCollect()}>
                Collect
              </Button>
              <Button size="sm" disabled={busy || !canWrite} onClick={() => void onLabHandover()}>
                Hand over to lab
              </Button>
              <Link href="/app/reception" className="text-sm text-sky-700 hover:underline self-center">
                Back
              </Link>
            </div>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
