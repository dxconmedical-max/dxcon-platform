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
      // Field queue only — AT_RECEPTION is owned by Reception desk collections.
      const data = await fetchCollectionQueue(
        { token: accessToken, organizationId: activeOrganizationId },
        {
          status: status || undefined,
          location: location || undefined,
          date: date || undefined,
          collector: collector || undefined,
          include_desk: false,
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
    <AppShell title="Hàng đợi lấy mẫu" workspacePath="/app/collector">
      <div className="space-y-6">
        <SectionHeader
          title="Việc lấy mẫu tại nhà"
          description="Chỉ hiện các ca lấy mẫu tại nhà. Yêu cầu từ phòng khám nằm ở Lễ tân → Yêu cầu lấy mẫu ngoài. Ca lấy mẫu tại quầy nằm ở Lễ tân → Lấy mẫu tại quầy."
          actions={
            <Button size="sm" variant="outline" onClick={() => void load()}>
              Làm mới
            </Button>
          }
        />

        <div className="grid grid-cols-1 gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:grid-cols-2 lg:grid-cols-4">
          <label className="block min-w-0 text-sm">
            <span className="mb-1 block text-slate-600">Trạng thái</span>
            <select
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">Đang chờ (mặc định)</option>
              <option value="REQUESTED">Mới yêu cầu</option>
              <option value="ASSIGNED">Đã phân công</option>
              <option value="VERIFIED">Đã xác minh</option>
              <option value="COLLECTED">Đã lấy mẫu</option>
              <option value="IN_TRANSIT">Đang vận chuyển</option>
              <option value="ARRIVED_AT_LAB">Đã đến phòng xét nghiệm</option>
              <option value="REJECTED">Bị từ chối</option>
              <option value="RECOLLECT_REQUIRED">Cần lấy lại mẫu</option>
            </select>
          </label>
          <label className="block min-w-0 text-sm">
            <span className="mb-1 block text-slate-600">Khu vực</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="Thành phố hoặc địa chỉ"
            />
          </label>
          <label className="block min-w-0 text-sm">
            <span className="mb-1 block text-slate-600">Ngày</span>
            <div className="w-full max-w-full overflow-hidden rounded-lg">
              <input
                type="date"
                className="block h-10 w-full min-w-0 max-w-full appearance-none rounded-lg border border-slate-300 px-3 py-2"
                style={{ minWidth: 0, width: "100%", maxWidth: "100%", boxSizing: "border-box" }}
                value={date}
                onChange={(e) => setDate(e.target.value)}
              />
            </div>
          </label>
          <label className="block min-w-0 text-sm">
            <span className="mb-1 block text-slate-600">Mã nhân viên lấy mẫu</span>
            <input
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
              value={collector}
              onChange={(e) => setCollector(e.target.value)}
              placeholder="Không bắt buộc"
            />
          </label>
        </div>

        {!canRead ? (
          <p className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            Bạn không có quyền xem hàng đợi lấy mẫu.
          </p>
        ) : (
          <DataState
            loading={loading}
            error={error}
            empty={!loading && items.length === 0}
            emptyLabel="Không có ca lấy mẫu nào khớp bộ lọc."
            onRetry={() => void load()}
          >
            <SimpleTable
              rows={items}
              rowKey={(row) => row.id}
              columns={[
                {
                  key: "patient",
                  label: "Bệnh nhân / đơn",
                  render: (row) => (
                    <div>
                      <div className="font-medium">
                        {row.job_info?.patient_name ||
                          row.booking?.patient_name ||
                          String((row.order as { patient_name?: string } | null)?.patient_name ?? "—")}
                      </div>
                      <div className="text-xs text-slate-500">
                        {row.job_info?.patient_phone ? `${row.job_info.patient_phone} · ` : ""}
                        {row.job_info?.order_code || row.booking?.booking_code || row.sample_code || row.id.slice(0, 8)}
                      </div>
                      {row.job_info && !row.job_info.order_found ? (
                        <div className="text-xs text-amber-700">Không tìm thấy đơn</div>
                      ) : null}
                    </div>
                  ),
                },
                {
                  key: "tests",
                  label: "Xét nghiệm / tiền",
                  render: (row) => {
                    const j = row.job_info;
                    if (!j || !j.order_found) return "—";
                    const names = j.tests.map((t) => t.test_name).filter(Boolean);
                    return (
                      <div className="max-w-xs text-xs">
                        <div>{names.length > 3 ? `${names.slice(0, 3).join(", ")} +${names.length - 3}` : names.join(", ") || "—"}</div>
                        <div className={j.due_amount ? "font-semibold text-red-600" : "text-emerald-700"}>
                          {j.due_amount ? `Còn thu ${Math.round(j.due_amount).toLocaleString("vi-VN")} ₫` : "Đã thanh toán"}
                        </div>
                      </div>
                    );
                  },
                },
                {
                  key: "mode",
                  label: "Hình thức",
                  render: (row) => String(row.collection_mode || "—"),
                },
                {
                  key: "location",
                  label: "Địa chỉ lấy mẫu",
                  render: (row) =>
                    row.pickup_address ||
                    row.collection_location ||
                    row.location_city ||
                    row.booking?.patient_address ||
                    "—",
                },
                {
                  key: "schedule",
                  label: "Lịch hẹn",
                  render: (row) =>
                    [row.requested_date, row.requested_time_window].filter(Boolean).join(" ") || "—",
                },
                {
                  key: "collector",
                  label: "Phân công",
                  render: (row) => row.collector_name || row.collector_id || "Chưa phân công",
                },
                {
                  key: "status",
                  label: "Trạng thái",
                  render: (row) => <StatusPill status={row.status} />,
                },
                {
                  key: "action",
                  label: "",
                  render: (row) => {
                    const terminal =
                      row.actionable === false ||
                      ["ARRIVED_AT_LAB", "RECEIVED", "REJECTED", "CANCELLED", "COMPLETED", "RELEASED"].includes(
                        String(row.status || "").toUpperCase(),
                      );
                    if (terminal) {
                      return <span className="text-xs text-slate-400">Đã đóng</span>;
                    }
                    return (
                      <Link
                        href={`/app/collector/workflow?id=${encodeURIComponent(row.id)}`}
                        className="text-sm font-medium text-sky-700 hover:underline"
                      >
                        Mở
                      </Link>
                    );
                  },
                },
              ]}
            />
          </DataState>
        )}
      </div>
    </AppShell>
  );
}
