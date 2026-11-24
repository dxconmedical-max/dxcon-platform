"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import {
  BOOKING_STATUSES,
  BOOKING_STATUS_LABELS,
  listBookingRequests,
  setBookingStatus,
  type BookingRequestItem,
  type BookingStatus,
} from "@/lib/api/publicBooking";

const SLOT_LABELS: Record<string, string> = {
  ANYTIME: "Giờ nào cũng được",
  MORNING: "Buổi sáng",
  AFTERNOON: "Buổi chiều",
};

export default function ReceptionBookingsPage() {
  const { accessToken, activeOrganizationId, role } = useAuth();
  const [filter, setFilter] = useState<BookingStatus>("NEW");
  const [items, setItems] = useState<BookingRequestItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const canWrite = ["RECEPTION", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN"].includes(role ?? "");

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await listBookingRequests(
        { token: accessToken, organizationId: activeOrganizationId },
        filter,
      );
      setItems(data.items);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, activeOrganizationId, filter]);

  useEffect(() => {
    const timer = setTimeout(() => void load(), 0);
    return () => clearTimeout(timer);
  }, [load]);

  async function update(id: string, status: BookingStatus) {
    if (!accessToken) return;
    setBusyId(id);
    setError(null);
    try {
      await setBookingStatus({ token: accessToken, organizationId: activeOrganizationId }, id, status);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <AppShell title="Yêu cầu đặt lịch" workspacePath="/app/reception">
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Yêu cầu đặt lịch từ website</h1>
          <p className="text-sm text-slate-600">
            Gọi lại khách để xác nhận, rồi tạo đơn trong quy trình tiếp nhận như bình thường.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {BOOKING_STATUSES.map((status) => (
            <Button
              key={status}
              size="sm"
              variant={status === filter ? "primary" : "outline"}
              onClick={() => setFilter(status)}
            >
              {BOOKING_STATUS_LABELS[status]}
            </Button>
          ))}
        </div>
        {error ? <p className="text-sm text-red-700">{error}</p> : null}
        {loading ? <p className="text-sm text-slate-500">Đang tải…</p> : null}
        {!loading && items.length === 0 ? (
          <p className="text-sm text-slate-500">Không có yêu cầu nào ở trạng thái “{BOOKING_STATUS_LABELS[filter]}”.</p>
        ) : null}
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.id} className="rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-medium">
                    {item.full_name} · <a className="text-teal-700" href={`tel:${item.phone}`}>{item.phone}</a>
                  </p>
                  <p className="text-sm text-slate-600">
                    {item.address}
                    {item.district ? `, ${item.district}` : ""}
                  </p>
                  <p className="text-sm text-slate-600">
                    {item.preferred_date ?? "Chưa chọn ngày"} · {SLOT_LABELS[item.preferred_slot] ?? item.preferred_slot}
                  </p>
                  {item.note ? <p className="text-sm text-slate-600">Ghi chú: {item.note}</p> : null}
                  <p className="mt-1 text-xs text-slate-400">
                    {item.reference} · {item.created_at ?? ""}
                    {item.handled_by ? ` · xử lý bởi ${item.handled_by}` : ""}
                    {item.internal_note ? ` · ${item.internal_note}` : ""}
                  </p>
                </div>
                {canWrite ? (
                  <div className="flex flex-wrap gap-2">
                    {(["CONTACTED", "SCHEDULED", "DONE", "CANCELLED", "SPAM"] as BookingStatus[])
                      .filter((s) => s !== item.status)
                      .map((s) => (
                        <Button key={s} size="sm" variant="outline" disabled={busyId === item.id} onClick={() => void update(item.id, s)}>
                          {BOOKING_STATUS_LABELS[s]}
                        </Button>
                      ))}
                    {!["DONE", "CANCELLED", "SPAM"].includes(item.status) ? (
                      <Link
                        href={`/app/reception/workflow?booking=${encodeURIComponent(item.id)}`}
                        className="inline-flex items-center rounded-lg bg-teal-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-teal-800"
                      >
                        Tạo đơn thu mẫu
                      </Link>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </AppShell>
  );
}
