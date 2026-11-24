"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import {
  fetchReleaseQueue,
  fetchReleasedReportHtml,
  releaseLabResult,
  type LabQueueRow,
} from "@/lib/api/labWorkflow";

import { DataState, SectionHeader, SimpleTable } from "../../reception/_components/ui";

export default function LabReleasePage() {
  const { accessToken, activeOrganizationId, role } = useAuth();
  const auth = useMemo(
    () => ({ token: accessToken, organizationId: activeOrganizationId }),
    [accessToken, activeOrganizationId],
  );
  const canRelease = ["DOCTOR", "LAB", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN"].includes(role ?? "");

  const [items, setItems] = useState<LabQueueRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [htmlPreview, setHtmlPreview] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setItems(await fetchReleaseQueue(auth));
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, auth]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onRelease(orderCode: string) {
    setBusy(orderCode);
    setError(null);
    setMessage(null);
    try {
      const data = await releaseLabResult(auth, orderCode);
      setMessage(
        `Released ${orderCode}. Email ready: ${String(data.email_ready ?? true)}. PDF/HTML ready: ${String(data.html_ready ?? true)}.`,
      );
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(null);
    }
  }

  async function onPreview(orderCode: string) {
    setBusy(orderCode);
    setError(null);
    try {
      const data = await fetchReleasedReportHtml(auth, orderCode);
      setHtmlPreview(String(data.html_content || ""));
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(null);
    }
  }

  function onDownload(orderCode: string) {
    if (!htmlPreview) return;
    const blob = new Blob([htmlPreview], { type: "text/html;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${orderCode}-report.html`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <AppShell title="Kết quả đã trả" workspacePath="/app/lab">
      <div className="space-y-5">
        <SectionHeader
          title="Trả kết quả"
          description="Phát hành kết quả đã được bác sĩ duyệt để bệnh nhân tải về, đánh dấu sẵn sàng gửi email và tạo file HTML/PDF."
          actions={
            <div className="flex gap-2">
              <Link href="/app/doctor/review" className="self-center text-sm text-sky-700 hover:underline">
                Hộp chờ bác sĩ
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
          emptyLabel="Chưa có kết quả đã duyệt hoặc đã trả."
          onRetry={() => void load()}
        >
          <SimpleTable
            rows={items}
            rowKey={(row) => row.order_code}
            columns={[
              { key: "order", label: "Đơn", render: (row) => row.order_code },
              {
                key: "patient",
                label: "Bệnh nhân",
                render: (row) => row.patient_name || "—",
              },
              { key: "status", label: "Trạng thái", render: (row) => row.status || "—" },
              {
                key: "email",
                label: "Sẵn sàng gửi email",
                render: (row) => (row.email_ready || row.status === "released" ? "Yes" : "No"),
              },
              {
                key: "actions",
                label: "Thao tác",
                render: (row) => (
                  <div className="flex flex-wrap gap-2">
                    {row.status !== "released" ? (
                      <Button
                        size="sm"
                        disabled={!canRelease || busy === row.order_code}
                        onClick={() => void onRelease(row.order_code)}
                      >
                        Trả kết quả
                      </Button>
                    ) : (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={busy === row.order_code}
                          onClick={() => void onPreview(row.order_code)}
                        >
                          PDF / HTML
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={!htmlPreview}
                          onClick={() => onDownload(row.order_code)}
                        >
                          Tải về
                        </Button>
                        <Link
                          href={`/app/patient/results?order=${encodeURIComponent(row.order_code)}`}
                          className="self-center text-xs text-sky-700 hover:underline"
                        >
                          Bệnh nhân xem
                        </Link>
                      </>
                    )}
                  </div>
                ),
              },
            ]}
          />
        </DataState>
        {htmlPreview ? (
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <p className="mb-2 text-sm font-medium text-slate-800">Xem trước báo cáo</p>
            <div
              className="max-h-96 overflow-auto text-sm"
              dangerouslySetInnerHTML={{ __html: htmlPreview }}
            />
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}
