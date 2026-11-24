"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import {
  fetchAiNotes,
  fetchMedicalQueue,
  type AiNotes,
  medicalReject,
  medicalReopen,
  medicalValidate,
  type LabQueueRow,
} from "@/lib/api/labWorkflow";

import { DataState, SectionHeader, SimpleTable } from "../../reception/_components/ui";

export default function DoctorMedicalValidationPage() {
  const { accessToken, activeOrganizationId, role } = useAuth();
  const auth = useMemo(
    () => ({ token: accessToken, organizationId: activeOrganizationId }),
    [accessToken, activeOrganizationId],
  );
  const canMedical = ["DOCTOR", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN"].includes(role ?? "");

  const [items, setItems] = useState<LabQueueRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [aiFor, setAiFor] = useState<string | null>(null);
  const [aiNotes, setAiNotes] = useState<AiNotes | null>(null);
  const [aiError, setAiError] = useState<string | null>(null);

  async function showAi(orderCode: string) {
    setAiFor(orderCode);
    setAiNotes(null);
    setAiError(null);
    try {
      setAiNotes(await fetchAiNotes(auth, orderCode));
    } catch (err) {
      setAiError(normalizeApiError(err));
    }
  }

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setItems(await fetchMedicalQueue(auth));
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, auth]);

  useEffect(() => {
    void load();
  }, [load]);

  async function run(
    orderCode: string,
    action: "approve" | "reject" | "reopen",
  ) {
    setBusy(orderCode);
    setError(null);
    setMessage(null);
    try {
      if (action === "approve") await medicalValidate(auth, orderCode, note || undefined);
      if (action === "reject") await medicalReject(auth, orderCode, note || undefined);
      if (action === "reopen") await medicalReopen(auth, orderCode, note || undefined);
      setMessage(`${action} completed for ${orderCode}`);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <AppShell title="Duyệt chuyên môn" workspacePath="/app/doctor">
      <div className="space-y-5">
        <SectionHeader
          title="Hộp kết quả chờ duyệt chuyên môn"
          description="Duyệt, từ chối hoặc mở lại kết quả đang chờ bác sĩ ký. Mọi thao tác được ghi vào nhật ký."
          actions={
            <div className="flex gap-2">
              <Link href="/app/lab/release" className="self-center text-sm text-sky-700 hover:underline">
                Bảng trả kết quả
              </Link>
              <Button size="sm" variant="outline" onClick={() => void load()}>
                Làm mới
              </Button>
            </div>
          }
        />
        {!canMedical ? (
          <p className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
            Cần vai trò bác sĩ hoặc quản trị để duyệt chuyên môn.
          </p>
        ) : null}
        <div>
          <Label htmlFor="doctor-note">Ghi chú (không bắt buộc)</Label>
          <Input id="doctor-note" value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
        <DataState
          loading={loading}
          error={error}
          empty={!loading && items.length === 0}
          emptyLabel="Không có kết quả nào chờ duyệt."
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
                render: (row) => row.patient_name || row.patient || "—",
              },
              { key: "status", label: "Trạng thái", render: (row) => row.status || "—" },
              {
                key: "actions",
                label: "Thao tác",
                render: (row) => (
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      disabled={!canMedical || busy === row.order_code}
                      onClick={() => void run(row.order_code, "approve")}
                    >
                      Duyệt
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={!canMedical || busy === row.order_code}
                      onClick={() => void run(row.order_code, "reject")}
                    >
                      Từ chối
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={!canMedical || busy === row.order_code}
                      onClick={() => void run(row.order_code, "reopen")}
                    >
                      Mở lại
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => void showAi(row.order_code)}>
                      Gợi ý AI
                    </Button>
                    <Link
                      href={`/app/lab/workflow?order=${encodeURIComponent(row.order_code)}`}
                      className="self-center text-xs text-sky-700 hover:underline"
                    >
                      Mở phòng xét nghiệm
                    </Link>
                  </div>
                ),
              },
            ]}
          />
        </DataState>
        {aiFor ? (
          <section className="space-y-3 rounded-xl border border-violet-200 bg-violet-50 p-4 text-sm">
            <div className="flex items-center justify-between">
              <h2 className="font-semibold text-violet-900">Gợi ý AI cho đơn {aiFor} (chỉ để tham khảo)</h2>
              <button className="text-xs text-violet-700 underline" onClick={() => setAiFor(null)}>
                Đóng
              </button>
            </div>
            {aiError ? <p className="text-red-700">{aiError}</p> : null}
            {!aiNotes && !aiError ? <p>Đang tạo gợi ý…</p> : null}
            {aiNotes ? (
              <>
                <p>{aiNotes.summary}</p>
                {aiNotes.considerations.length > 0 ? (
                  <div>
                    <p className="font-medium">Cần cân nhắc</p>
                    <ul className="list-disc pl-5">
                      {aiNotes.considerations.map((c, i) => (
                        <li key={i}>
                          <strong>{c.test_name}</strong>: {c.consideration}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {aiNotes.suggested_tests.length > 0 ? (
                  <div>
                    <p className="font-medium">Xét nghiệm có thể cần làm tiếp</p>
                    <ul className="list-disc pl-5">
                      {aiNotes.suggested_tests.map((t, i) => (
                        <li key={i}>
                          {t.test} <span className="text-violet-700">(do {t.because})</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
                {aiNotes.no_rule_for.length > 0 ? (
                  <p className="text-xs text-slate-600">
                    Chưa có quy tắc gợi ý cho: {aiNotes.no_rule_for.join(", ")}.
                  </p>
                ) : null}
                <p className="text-xs italic text-slate-700">{aiNotes.disclaimer}</p>
              </>
            ) : null}
          </section>
        ) : null}
      </div>
    </AppShell>
  );
}
