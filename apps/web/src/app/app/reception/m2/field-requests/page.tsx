"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { apiRequest } from "@/services/api";
import { normalizeApiError } from "@/lib/errors";
import {
  assignCollector,
  fetchAssignableCollectors,
  unassignCollector,
  type AssignableCollector,
  type SampleCollectionItem,
} from "@/lib/api/sampleCollection";

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
  const [collectors, setCollectors] = useState<AssignableCollector[]>([]);
  const [selectedCollector, setSelectedCollector] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const auth = { token: accessToken, organizationId: activeOrganizationId };

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [body, collectorRows] = await Promise.all([
        apiRequest<{ success: boolean; data: FieldQueue }>(
          "/api/v1/reception/workspace/field-collection-requests",
          { method: "GET", token: accessToken, organizationId: activeOrganizationId },
        ),
        fetchAssignableCollectors(auth),
      ]);
      setItems(body.data?.items ?? []);
      setCollectors(collectorRows);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeOrganizationId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onAssign(row: SampleCollectionItem) {
    const collectionId = String(row.sample_collection_id || row.id);
    const collectorId = selectedCollector[row.id] || collectors[0]?.id;
    if (!collectorId) {
      setError("Hãy chọn nhân viên thu mẫu trước.");
      return;
    }
    const collector = collectors.find((c) => c.id === collectorId);
    setBusyId(row.id);
    setError(null);
    setMessage(null);
    try {
      await assignCollector(auth, collectionId, {
        collector_id: collectorId,
        collector_name: collector?.full_name || collector?.email,
      });
      setMessage(`Assigned ${collector?.full_name || collectorId} to job.`);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusyId(null);
    }
  }

  async function onRelease(row: SampleCollectionItem) {
    const collectionId = String(row.sample_collection_id || row.id);
    setBusyId(row.id);
    setError(null);
    setMessage(null);
    try {
      await unassignCollector(auth, collectionId);
      setMessage("Đã hủy phân công.");
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell title="Yêu cầu thu mẫu tại nhà / phòng khám" workspacePath="/app/reception">
      <div className="space-y-6">
        <SectionHeader
          title="Yêu cầu thu mẫu tại nhà / phòng khám"
          description="Yêu cầu thu mẫu tại nhà và tại phòng khám. Phân công hoặc đổi nhân viên; việc tại nhà sẽ hiện trong hàng đợi của nhân viên thu mẫu."
          actions={
            <div className="flex gap-2">
              <Link
                href="/app/collector/queue"
                className="self-center text-sm font-medium text-sky-700 hover:underline"
              >
                Mở hàng đợi thu mẫu
              </Link>
              <Button size="sm" variant="outline" onClick={() => void load()}>
                Làm mới
              </Button>
            </div>
          }
        />
        {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
        <DataState
          loading={loading}
          error={error}
          empty={!loading && items.length === 0}
          emptyLabel="Không có yêu cầu thu mẫu nào."
          onRetry={() => void load()}
        >
          <SimpleTable
            rows={items}
            rowKey={(row) => row.id}
            columns={[
              {
                key: "patient",
                label: "Bệnh nhân",
                render: (row) =>
                  row.booking?.patient_name ||
                  String((row.order as { patient_name?: string } | null)?.patient_name ?? "—"),
              },
              {
                key: "order",
                label: "Đơn",
                render: (row) =>
                  row.booking?.booking_code ||
                  String((row.order as { order_code?: string } | null)?.order_code ?? "—"),
              },
              {
                key: "address",
                label: "Địa chỉ",
                render: (row) =>
                  row.pickup_address ||
                  row.clinic_name ||
                  row.collection_location ||
                  row.booking?.patient_address ||
                  "—",
              },
              {
                key: "date",
                label: "Ngày yêu cầu",
                render: (row) => row.requested_date || "—",
              },
              {
                key: "status",
                label: "Trạng thái",
                render: (row) => <StatusPill status={row.status} />,
              },
              {
                key: "collector",
                label: "Nhân viên được phân công",
                render: (row) => row.collector_name || "—",
              },
              {
                key: "actions",
                label: "Thao tác",
                render: (row) => (
                  <div className="flex flex-wrap items-center gap-2">
                    <select
                      className="rounded border border-slate-300 px-2 py-1 text-xs"
                      value={selectedCollector[row.id] || ""}
                      onChange={(e) =>
                        setSelectedCollector((prev) => ({ ...prev, [row.id]: e.target.value }))
                      }
                      aria-label={`Collector for ${row.id}`}
                    >
                      <option value="">Chọn nhân viên thu mẫu</option>
                      {collectors.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.full_name || c.email}
                        </option>
                      ))}
                    </select>
                    <Button
                      size="sm"
                      disabled={busyId === row.id}
                      onClick={() => void onAssign(row)}
                    >
                      {row.collector_id ? "Reassign" : "Assign"}
                    </Button>
                    {row.collector_id ? (
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={busyId === row.id}
                        onClick={() => void onRelease(row)}
                      >
                        Trả kết quả
                      </Button>
                    ) : null}
                  </div>
                ),
              },
            ]}
          />
        </DataState>
      </div>
    </AppShell>
  );
}
