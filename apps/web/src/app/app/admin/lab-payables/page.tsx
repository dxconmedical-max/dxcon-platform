"use client";

import { useCallback, useEffect, useState } from "react";

import { PriceSheetPanel } from "@/components/admin/PriceSheetPanel";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import { formatVnd } from "@/lib/format";
import {
  addLab,
  addLabPayment,
  assignOrders,
  bulkSetCosts,
  createLabStatement,
  downloadCostTemplate,
  getLab,
  downloadStatementExcel,
  getLabStatement,
  getLabs,
  getRouting,
  getUnassigned,
  listCosts,
  previewLabStatement,
  recalcLab,
  searchOrganizations,
  setRouting,
  uploadCostFile,
  voidLabStatement,
  type CostRow,
  type LabDetail,
  type LabRow,
  type LabStatementDetail,
  type OrgHit,
  type RoutingData,
  type UnassignedOrder,
} from "@/lib/api/labPayables";

type Tab = "overview" | "costs" | "statements" | "payments";
const TABS: { key: Tab; label: string }[] = [
  { key: "overview", label: "Tổng quan" },
  { key: "costs", label: "Giá nhập" },
  { key: "statements", label: "Đối soát" },
  { key: "payments", label: "Đã chuyển khoản" },
];
const INPUT = "rounded-lg border border-slate-300 px-3 py-1.5 text-sm";

export default function LabPayablesPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = accessToken ? { token: accessToken, organizationId: activeOrganizationId } : null;
  const [labs, setLabs] = useState<LabRow[]>([]);
  const [totals, setTotals] = useState({ out: 0, unbilled: 0 });
  const [routing, setRoutingData] = useState<RoutingData | null>(null);
  const [unassigned, setUnassigned] = useState<UnassignedOrder[]>([]);
  const [pick, setPick] = useState<Record<string, boolean>>({});
  const [assignLab, setAssignLab] = useState("");
  const [orgQ, setOrgQ] = useState("");
  const [orgHits, setOrgHits] = useState<OrgHit[]>([]);

  const [labId, setLabId] = useState<string | null>(null);
  const [data, setData] = useState<LabDetail | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [cq, setCq] = useState("");
  const [onlyPriced, setOnlyPriced] = useState(false);
  const [costs, setCosts] = useState<CostRow[]>([]);
  const [pricedCount, setPricedCount] = useState(0);

  const [ps, setPs] = useState("");
  const [pe, setPe] = useState("");
  const [preview, setPreview] = useState<{ order_count: number; total_amount: number; margin: number; missing_cost_orders: number } | null>(null);
  const [detail, setDetail] = useState<LabStatementDetail | null>(null);

  const [payAmount, setPayAmount] = useState("");
  const [payDate, setPayDate] = useState("");
  const [payMethod, setPayMethod] = useState("");
  const [payRef, setPayRef] = useState("");

  async function guard(fn: () => Promise<void>, ok?: string) {
    setBusy(true);
    setError(null);
    setNotice(null);
    try {
      await fn();
      if (ok) setNotice(ok);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  const loadList = useCallback(async () => {
    if (!accessToken) return;
    const c = { token: accessToken, organizationId: activeOrganizationId };
    try {
      const [l, r, u] = await Promise.all([getLabs(c), getRouting(c), getUnassigned(c)]);
      setLabs(l.labs);
      setTotals({ out: l.total_outstanding, unbilled: l.total_unbilled });
      setRoutingData(r);
      setUnassigned(u);
    } catch (err) {
      setError(normalizeApiError(err));
    }
  }, [accessToken, activeOrganizationId]);

  useEffect(() => {
    const timer = setTimeout(() => void loadList(), 0);
    return () => clearTimeout(timer);
  }, [loadList]);

  async function loadLab(id: string) {
    if (!ctx) return;
    setData(await getLab(ctx, id));
  }

  async function openLab(id: string) {
    setLabId(id);
    setTab("overview");
    setDetail(null);
    setPreview(null);
    setCosts([]);
    await guard(() => loadLab(id));
  }

  async function refresh() {
    if (labId) await loadLab(labId);
    await loadList();
  }

  async function searchCosts() {
    if (!ctx || !labId) return;
    await guard(async () => {
      const r = await listCosts(ctx, labId, cq.trim(), onlyPriced);
      setCosts(r.tests);
      setPricedCount(r.priced_count);
    });
  }

  const period = ps && pe ? { period_start: ps, period_end: pe } : null;
  const selectedCodes = Object.keys(pick).filter((k) => pick[k]);

  return (
    <AppShell title="Công nợ phải trả phòng xét nghiệm" workspacePath="/app/admin">
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Giá nhập và công nợ phải trả phòng xét nghiệm</h1>
          <p className="text-sm text-slate-600">
            Nhập giá do phòng xét nghiệm báo, gán ca cho phòng xét nghiệm thực hiện, xem lãi của DxCon và theo dõi số tiền phải trả.
          </p>
        </div>
        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        {notice ? <p className="rounded-lg bg-green-50 p-2 text-sm text-green-800">{notice}</p> : null}

        {!labId ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-xl border border-slate-200 bg-white p-3">
                <p className="text-xs text-slate-500">Đang nợ phòng xét nghiệm (đã đối soát)</p>
                <p className="text-lg font-semibold">{formatVnd(totals.out)}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-3">
                <p className="text-xs text-slate-500">Chưa đối soát (giá nhập)</p>
                <p className="text-lg font-semibold">{formatVnd(totals.unbilled)}</p>
              </div>
            </div>

            <section className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="font-medium">Phòng xét nghiệm</h2>
              {labs.length === 0 ? <p className="text-sm text-slate-500">Chưa có phòng xét nghiệm nào. Thêm ở phần bên dưới.</p> : null}
              <ul className="space-y-2">
                {labs.map((l) => (
                  <li key={l.organization_id} className="rounded-lg border border-slate-200 p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="font-medium">{l.organization_name}</p>
                      <Button size="sm" variant="outline" onClick={() => void openLab(l.organization_id)}>
                        Mở
                      </Button>
                    </div>
                    <p className="mt-1 text-xs text-slate-600">
                      Còn nợ {formatVnd(l.outstanding)} · Chưa đối soát {l.unbilled_orders} ca ({formatVnd(l.unbilled_cost)}) · Lãi dự kiến {formatVnd(l.unbilled_margin)}
                    </p>
                    {l.missing_cost_orders ? (
                      <p className="text-xs text-amber-700">{l.missing_cost_orders} ca thiếu giá nhập, chưa tính vào đối soát.</p>
                    ) : null}
                  </li>
                ))}
              </ul>
              <div className="space-y-2 border-t border-slate-100 pt-3">
                <p className="text-sm font-medium">Thêm phòng xét nghiệm</p>
                <div className="flex gap-2">
                  <input
                    value={orgQ}
                    onChange={(e) => setOrgQ(e.target.value)}
                    placeholder="Tên hoặc mã đơn vị (ví dụ PXN 548)"
                    aria-label="Tìm đơn vị"
                    className={`${INPUT} flex-1`}
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={busy}
                    onClick={() => ctx && void guard(async () => setOrgHits(await searchOrganizations(ctx, orgQ.trim())))}
                  >
                    Tìm
                  </Button>
                </div>
                <ul className="space-y-1">
                  {orgHits.map((o) => (
                    <li key={o.id} className="flex items-center justify-between gap-2 text-sm">
                      <span>
                        {o.name} <span className="text-xs text-slate-500">({o.code})</span>
                      </span>
                      <Button
                        size="sm"
                        disabled={busy}
                        onClick={() =>
                          ctx &&
                          void guard(async () => {
                            await addLab(ctx, o.id);
                            setOrgHits([]);
                            await loadList();
                          }, `Đã thêm ${o.name} làm phòng xét nghiệm.`)
                        }
                      >
                        Thêm
                      </Button>
                    </li>
                  ))}
                </ul>
              </div>
            </section>

            <section className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="font-medium">Gửi mẫu đến phòng xét nghiệm nào</h2>
              <p className="text-xs text-slate-500">Ca mới tự gán theo cài đặt của phòng khám đó. Nếu phòng khám chưa chọn thì dùng phòng xét nghiệm mặc định.</p>
              {routing ? (
                <div className="space-y-2">
                  <label className="flex flex-wrap items-center gap-2 text-sm">
                    <span className="w-48 font-medium">Mặc định (cả khách vãng lai)</span>
                    <select
                      aria-label="Phòng xét nghiệm mặc định"
                      className={INPUT}
                      value={routing.default_lab_id ?? ""}
                      disabled={busy}
                      onChange={(e) => ctx && void guard(async () => { await setRouting(ctx, "DEFAULT", e.target.value || null); await loadList(); }, "Đã lưu.")}
                    >
                      <option value="">Chưa chọn</option>
                      {routing.labs.map((l) => (
                        <option key={l.id} value={l.id}>{l.name}</option>
                      ))}
                    </select>
                  </label>
                  {routing.clinics.map((c) => (
                    <label key={c.id} className="flex flex-wrap items-center gap-2 text-sm">
                      <span className="w-48">{c.name}</span>
                      <select
                        aria-label={`Phòng xét nghiệm của ${c.name}`}
                        className={INPUT}
                        value={c.lab_id ?? ""}
                        disabled={busy}
                        onChange={(e) => ctx && void guard(async () => { await setRouting(ctx, c.id, e.target.value || null); await loadList(); }, "Đã lưu.")}
                      >
                        <option value="">Theo mặc định</option>
                        {routing.labs.map((l) => (
                          <option key={l.id} value={l.id}>{l.name}</option>
                        ))}
                      </select>
                    </label>
                  ))}
                </div>
              ) : null}
            </section>

            <section className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="font-medium">Ca chưa gán phòng xét nghiệm</h2>
              {unassigned.length === 0 ? <p className="text-sm text-slate-500">Mọi ca đều đã được gán.</p> : null}
              <ul className="space-y-1">
                {unassigned.map((o) => (
                  <li key={o.order_code} className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      aria-label={`Chọn ${o.order_code}`}
                      checked={!!pick[o.order_code]}
                      onChange={(e) => setPick({ ...pick, [o.order_code]: e.target.checked })}
                    />
                    <span className="font-mono text-xs">{o.order_code}</span>
                    <span className="flex-1">{o.patient_name} · {o.clinic_name}</span>
                    <span>{formatVnd(o.total_amount)}</span>
                  </li>
                ))}
              </ul>
              {unassigned.length ? (
                <div className="flex flex-wrap items-center gap-2">
                  <select aria-label="Gán cho phòng xét nghiệm" className={INPUT} value={assignLab} onChange={(e) => setAssignLab(e.target.value)}>
                    <option value="">Chọn phòng xét nghiệm</option>
                    {labs.map((l) => (
                      <option key={l.organization_id} value={l.organization_id}>{l.organization_name}</option>
                    ))}
                  </select>
                  <Button
                    size="sm"
                    disabled={busy || !assignLab || selectedCodes.length === 0}
                    onClick={() =>
                      ctx &&
                      void guard(async () => {
                        const r = await assignOrders(ctx, assignLab, selectedCodes);
                        setPick({});
                        await loadList();
                        setNotice(`Đã gán ${r.assigned} ca.`);
                      })
                    }
                  >
                    Gán {selectedCodes.length} ca đã chọn
                  </Button>
                </div>
              ) : null}
            </section>
          </div>
        ) : (
          <div className="space-y-4">
            <Button size="sm" variant="outline" onClick={() => { setLabId(null); setData(null); void loadList(); }}>
              ← Danh sách phòng xét nghiệm
            </Button>
            {data ? <h2 className="text-lg font-semibold">{data.lab.name}</h2> : null}
            <div className="flex flex-wrap gap-2">
              {TABS.map((t) => (
                <button
                  key={t.key}
                  type="button"
                  onClick={() => setTab(t.key)}
                  className={`rounded-full px-3 py-1 text-sm ${tab === t.key ? "bg-slate-900 text-white" : "bg-slate-100"}`}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {data && tab === "overview" ? (
              <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {[
                    ["Đã đối soát", data.summary.billed],
                    ["Đã chuyển khoản", data.summary.paid],
                    ["Còn nợ", data.summary.outstanding],
                    ["Chưa đối soát (giá nhập)", data.summary.unbilled_cost],
                  ].map(([label, v]) => (
                    <div key={String(label)} className="rounded-lg bg-slate-50 p-2">
                      <p className="text-xs text-slate-500">{label}</p>
                      <p className="text-sm font-semibold">{formatVnd(Number(v))}</p>
                    </div>
                  ))}
                </div>
                <p className="text-sm">
                  {data.summary.unbilled_orders} ca chưa đối soát, lãi dự kiến của DxCon {formatVnd(data.summary.unbilled_margin)}.
                </p>
                {data.summary.missing_cost_orders ? (
                  <p className="text-sm text-amber-700">
                    {data.summary.missing_cost_orders} ca thiếu giá nhập. Nhập giá ở tab “Giá nhập” rồi bấm “Tính lại giá nhập các ca”.
                  </p>
                ) : null}
                <Button
                  size="sm"
                  variant="outline"
                  disabled={busy}
                  onClick={() => ctx && labId && void guard(async () => { const r = await recalcLab(ctx, labId); await refresh(); setNotice(`Đã tính lại ${r.recalculated} ca.`); })}
                >
                  Tính lại giá nhập các ca
                </Button>
              </div>
            ) : null}

            {tab === "costs" ? (
              <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
                {ctx && labId ? (
                  <PriceSheetPanel
                    heading="Nhập nhanh giá nhập của phòng xét nghiệm này"
                    priceWord="giá nhập"
                    onPaste={(t, apply) => bulkSetCosts(ctx, labId, t, apply)}
                    onFile={(f, apply) => uploadCostFile(ctx, labId, f, apply)}
                    onTemplate={() => downloadCostTemplate(ctx, labId)}
                    onApplied={() => searchCosts()}
                  />
                ) : null}
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    value={cq}
                    onChange={(e) => setCq(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && void searchCosts()}
                    placeholder="Mã hoặc tên xét nghiệm"
                    aria-label="Tìm xét nghiệm"
                    className={`${INPUT} flex-1`}
                  />
                  <label className="flex items-center gap-1 text-sm">
                    <input type="checkbox" checked={onlyPriced} onChange={(e) => setOnlyPriced(e.target.checked)} /> Chỉ xét nghiệm đã có giá nhập
                  </label>
                  <Button size="sm" variant="outline" disabled={busy} onClick={() => void searchCosts()}>
                    Tìm
                  </Button>
                </div>
                {costs.length ? <p className="text-xs text-slate-500">Đã có giá nhập cho {pricedCount} xét nghiệm.</p> : null}
                <ul className="divide-y divide-slate-100">
                  {costs.map((c) => (
                    <li key={c.id} className="flex flex-wrap items-center justify-between gap-2 py-2 text-sm">
                      <span>
                        <span className="font-mono text-xs">{c.code}</span> {c.name}
                      </span>
                      <span className="text-xs text-slate-600">
                        Giá public {formatVnd(c.list_price)} · {c.cost === null ? "Chưa có giá nhập" : `Giá nhập ${formatVnd(c.cost)}`}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {data && tab === "statements" ? (
              <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
                <div className="flex flex-wrap items-end gap-2">
                  <label className="text-xs">Từ ngày<input type="date" value={ps} onChange={(e) => { setPs(e.target.value); setPreview(null); }} className={`${INPUT} block`} /></label>
                  <label className="text-xs">Đến ngày<input type="date" value={pe} onChange={(e) => { setPe(e.target.value); setPreview(null); }} className={`${INPUT} block`} /></label>
                  <Button size="sm" variant="outline" disabled={busy || !period} onClick={() => ctx && labId && period && void guard(async () => setPreview(await previewLabStatement(ctx, labId, period)))}>
                    Xem trước
                  </Button>
                  <Button
                    size="sm"
                    disabled={busy || !period || !preview || preview.order_count === 0}
                    onClick={() => ctx && labId && period && void guard(async () => { await createLabStatement(ctx, labId, period); setPreview(null); await refresh(); }, "Đã chốt bảng đối soát.")}
                  >
                    Chốt đối soát
                  </Button>
                </div>
                {preview ? (
                  <p className="text-sm">
                    {preview.order_count} ca, phải trả {formatVnd(preview.total_amount)}, lãi của DxCon {formatVnd(preview.margin)}.
                    {preview.missing_cost_orders ? ` ${preview.missing_cost_orders} ca thiếu giá nhập nên chưa tính.` : ""}
                  </p>
                ) : null}
                <ul className="space-y-2">
                  {data.statements.map((s) => (
                    <li key={s.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="font-medium">{s.statement_no}{s.status === "void" ? " (đã hủy)" : ""}</span>
                        <span>{formatVnd(s.total_amount)}</span>
                      </div>
                      <p className="text-xs text-slate-500">{s.period_start} → {s.period_end} · {s.order_count} ca</p>
                      {s.status !== "void" ? (
                        <div className="mt-2 flex gap-2">
                          <Button size="sm" variant="outline" disabled={busy} onClick={() => ctx && labId && void guard(async () => setDetail(await getLabStatement(ctx, labId, s.id)))}>
                            Xem chi tiết
                          </Button>
                          <Button size="sm" variant="outline" disabled={busy} onClick={() => ctx && labId && void guard(async () => downloadStatementExcel(ctx, labId, s.id))}>
                            Xuất Excel
                          </Button>
                          <Button size="sm" variant="outline" disabled={busy} onClick={() => ctx && labId && void guard(async () => { await voidLabStatement(ctx, labId, s.id); setDetail(null); await refresh(); }, "Đã hủy bảng đối soát.")}>
                            Hủy
                          </Button>
                        </div>
                      ) : null}
                    </li>
                  ))}
                </ul>
                {detail ? (
                  <div className="rounded-lg bg-slate-50 p-3 text-sm">
                    <p className="font-medium">{detail.statement_no} · {detail.lab_name}</p>
                    <ul className="mt-1 max-h-72 space-y-1 overflow-auto text-xs">
                      {detail.lines.map((l) => (
                        <li key={l.order_code} className="flex justify-between gap-2">
                          <span>{l.order_code} · {l.patient_name}</span>
                          <span>{formatVnd(l.amount)}</span>
                        </li>
                      ))}
                    </ul>
                    <p className="mt-2 font-medium">Tổng phải trả: {formatVnd(detail.total_amount)}</p>
                  </div>
                ) : null}
              </div>
            ) : null}

            {data && tab === "payments" ? (
              <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
                <div className="flex flex-wrap items-end gap-2">
                  <label className="text-xs">Số tiền<input value={payAmount} onChange={(e) => setPayAmount(e.target.value)} inputMode="numeric" className={`${INPUT} block`} /></label>
                  <label className="text-xs">Ngày chuyển<input type="date" value={payDate} onChange={(e) => setPayDate(e.target.value)} className={`${INPUT} block`} /></label>
                  <label className="text-xs">Hình thức<input value={payMethod} onChange={(e) => setPayMethod(e.target.value)} placeholder="Chuyển khoản" className={`${INPUT} block`} /></label>
                  <label className="text-xs">Số tham chiếu<input value={payRef} onChange={(e) => setPayRef(e.target.value)} className={`${INPUT} block`} /></label>
                  <Button
                    size="sm"
                    disabled={busy || !payAmount || !payDate}
                    onClick={() =>
                      ctx && labId &&
                      void guard(async () => {
                        await addLabPayment(ctx, labId, { amount: Number(payAmount.replace(/[^\d.]/g, "")), paid_at: payDate, method: payMethod || undefined, reference: payRef || undefined });
                        setPayAmount(""); setPayDate(""); setPayMethod(""); setPayRef("");
                        await refresh();
                      }, "Đã ghi nhận khoản chuyển.")
                    }
                  >
                    Ghi nhận
                  </Button>
                </div>
                <ul className="divide-y divide-slate-100 text-sm">
                  {data.payments.map((p) => (
                    <li key={p.id} className="flex flex-wrap justify-between gap-2 py-2">
                      <span>{p.paid_at} · {p.method ?? "—"}{p.reference ? ` · ${p.reference}` : ""}</span>
                      <span>{formatVnd(p.amount)}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </AppShell>
  );
}
