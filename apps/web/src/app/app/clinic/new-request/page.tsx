"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import {
  getClinicOrderStatus,
  listClinicSlips,
  searchClinicTests,
  submitClinicSlip,
  type CatalogTest,
  type ClinicSlip,
} from "@/lib/api/clinicOrders";

const STATUS_VI = { NEW: "Chờ DxCon duyệt", APPROVED: "Đã tạo đơn", REJECTED: "Bị từ chối" } as const;

export default function ClinicNewRequestPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = accessToken ? { token: accessToken, organizationId: activeOrganizationId } : null;

  const [allowed, setAllowed] = useState<boolean | null>(null);
  const [name, setName] = useState("");
  const [year, setYear] = useState("");
  const [tubes, setTubes] = useState("1");
  const [picked, setPicked] = useState<CatalogTest[]>([]);
  const [q, setQ] = useState("");
  const [found, setFound] = useState<CatalogTest[]>([]);
  const [slips, setSlips] = useState<ClinicSlip[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  const loadSlips = useCallback(async () => {
    if (!accessToken) return;
    try {
      setSlips(await listClinicSlips({ token: accessToken, organizationId: activeOrganizationId }));
    } catch (err) {
      setError(normalizeApiError(err));
    }
  }, [accessToken, activeOrganizationId]);

  useEffect(() => {
    if (!accessToken) return;
    let alive = true;
    void getClinicOrderStatus({ token: accessToken, organizationId: activeOrganizationId })
      .then((s) => {
        if (!alive) return;
        setAllowed(s.enabled && s.can_submit);
        if (s.enabled && s.can_submit) void loadSlips();
      })
      .catch((err) => alive && setError(normalizeApiError(err)));
    return () => {
      alive = false;
    };
  }, [accessToken, activeOrganizationId, loadSlips]);

  useEffect(() => {
    if (!ctx || !allowed || q.trim().length < 2) {
      const clear = setTimeout(() => setFound([]), 0);
      return () => clearTimeout(clear);
    }
    const timer = setTimeout(() => {
      void searchClinicTests(ctx, q.trim())
        .then(setFound)
        .catch((err) => setError(normalizeApiError(err)));
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, allowed, accessToken, activeOrganizationId]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!ctx) return;
    setError(null);
    setDone(null);
    if (picked.length === 0) {
      setError("Vui lòng chọn ít nhất một xét nghiệm.");
      return;
    }
    setBusy(true);
    try {
      const slip = await submitClinicSlip(ctx, {
        patient_name: name.trim(),
        birth_year: Number(year),
        tube_count: Number(tubes),
        test_ids: picked.map((t) => t.id),
      });
      setDone(slip.reference);
      setName("");
      setYear("");
      setTubes("1");
      setPicked([]);
      setQ("");
      await loadSlips();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell title="Phiếu chỉ định" workspacePath="/app/clinic">
      <div className="space-y-6">
        <div>
          <h1 className="text-xl font-semibold">Gửi phiếu chỉ định xét nghiệm</h1>
          <p className="text-sm text-slate-600">Nhập họ tên, năm sinh, xét nghiệm và số ống mẫu. DxCon sẽ duyệt rồi tạo đơn.</p>
        </div>
        {allowed === false ? (
          <p className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
            Phòng khám chưa được bật chức năng tự chỉ định, hoặc tài khoản này không có quyền gửi phiếu. Vui lòng liên hệ DxCon.
          </p>
        ) : null}
        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        {done ? <p className="rounded-xl bg-teal-50 p-3 text-sm text-teal-800">Đã gửi phiếu {done}. DxCon sẽ duyệt sớm.</p> : null}
        {allowed ? (
          <form onSubmit={onSubmit} className="space-y-4 rounded-2xl border border-slate-200 bg-white p-5">
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="sm:col-span-2">
                <Label htmlFor="pname">Họ tên bệnh nhân *</Label>
                <Input id="pname" required maxLength={120} value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="byear">Năm sinh *</Label>
                <Input id="byear" type="number" inputMode="numeric" required min={1900} max={new Date().getFullYear()} placeholder="1985" value={year} onChange={(e) => setYear(e.target.value)} />
              </div>
            </div>
            <div>
              <Label htmlFor="tsearch">Loại xét nghiệm *</Label>
              <Input id="tsearch" placeholder="Gõ tên hoặc mã, ví dụ: glucose" value={q} onChange={(e) => setQ(e.target.value)} />
              {found.length > 0 ? (
                <ul className="mt-2 max-h-52 overflow-auto rounded-lg border border-slate-200">
                  {found
                    .filter((t) => !picked.some((p) => p.id === t.id))
                    .map((t) => (
                      <li key={t.id}>
                        <button
                          type="button"
                          className="block w-full px-3 py-2 text-left text-sm hover:bg-slate-50"
                          onClick={() => {
                            setPicked((p) => [...p, t]);
                            setQ("");
                          }}
                        >
                          {t.name} <span className="text-slate-400">({t.code})</span>
                        </button>
                      </li>
                    ))}
                </ul>
              ) : null}
              {picked.length > 0 ? (
                <div className="mt-2 flex flex-wrap gap-2">
                  {picked.map((t) => (
                    <span key={t.id} className="inline-flex items-center gap-1 rounded-full bg-teal-50 px-3 py-1 text-sm text-teal-800">
                      {t.name}
                      <button type="button" aria-label={`Bỏ ${t.name}`} className="px-1" onClick={() => setPicked((p) => p.filter((x) => x.id !== t.id))}>
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
            <div className="max-w-40">
              <Label htmlFor="tubes">Số ống mẫu *</Label>
              <Input id="tubes" type="number" inputMode="numeric" required min={1} max={20} value={tubes} onChange={(e) => setTubes(e.target.value)} />
            </div>
            <Button type="submit" disabled={busy}>
              {busy ? "Đang gửi…" : "Gửi phiếu"}
            </Button>
          </form>
        ) : null}
        {slips.length > 0 ? (
          <section>
            <h2 className="mb-2 text-sm font-semibold">Phiếu đã gửi</h2>
            <ul className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white">
              {slips.map((s) => (
                <li key={s.id} className="p-3 text-sm">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium">{s.patient_name} · {s.birth_year}</span>
                    <span className="text-xs">{STATUS_VI[s.status]}</span>
                  </div>
                  <div className="text-slate-500">
                    {s.reference} · {s.tests.map((t) => t.name).join(", ")} · {s.tube_count} ống
                    {s.order_code ? ` · đơn ${s.order_code}` : ""}
                    {s.reject_reason ? ` · lý do: ${s.reject_reason}` : ""}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>
    </AppShell>
  );
}
