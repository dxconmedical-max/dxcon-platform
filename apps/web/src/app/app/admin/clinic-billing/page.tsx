"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import { formatVnd } from "@/lib/format";
import {
  addPayment,
  createStatement,
  downloadContract,
  getClinicBilling,
  getReceivables,
  getStatement,
  listClinicPrices,
  previewStatement,
  saveSettings,
  setClinicPrice,
  uploadContract,
  voidStatement,
  type Aging,
  type ClinicBilling,
  type PriceRow,
  type ReceivableRow,
  type StatementDetail,
} from "@/lib/api/clinicBilling";

type Tab = "overview" | "contracts" | "prices" | "statements" | "payments";
const TABS: { key: Tab; label: string }[] = [
  { key: "overview", label: "Tổng quan" },
  { key: "contracts", label: "Hợp đồng" },
  { key: "prices", label: "Bảng giá" },
  { key: "statements", label: "Kết toán" },
  { key: "payments", label: "Thanh toán" },
];
const INPUT = "rounded-lg border border-slate-300 px-3 py-1.5 text-sm";

function AgingRow({ aging }: { aging: Aging }) {
  const cells: [string, number][] = [
    ["Chưa đến hạn", aging.current],
    ["Quá 1–30 ngày", aging.d1_30],
    ["Quá 31–60 ngày", aging.d31_60],
    ["Quá trên 60 ngày", aging.d60_plus],
  ];
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
      {cells.map(([label, v]) => (
        <div key={label} className="rounded-lg bg-slate-50 p-2">
          <p className="text-xs text-slate-500">{label}</p>
          <p className="text-sm font-semibold">{formatVnd(v)}</p>
        </div>
      ))}
    </div>
  );
}

export default function ClinicBillingPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = accessToken ? { token: accessToken, organizationId: activeOrganizationId } : null;
  const [rows, setRows] = useState<ReceivableRow[]>([]);
  const [totals, setTotals] = useState({ out: 0, unbilled: 0 });
  const [orgId, setOrgId] = useState<string | null>(null);
  const [data, setData] = useState<ClinicBilling | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // settings form
  const [disc, setDisc] = useState("0");
  const [terms, setTerms] = useState("30");
  // prices
  const [pq, setPq] = useState("");
  const [onlyCustom, setOnlyCustom] = useState(false);
  const [prices, setPrices] = useState<PriceRow[]>([]);
  const [priceEdit, setPriceEdit] = useState<Record<string, string>>({});
  // statements
  const [ps, setPs] = useState("");
  const [pe, setPe] = useState("");
  const [preview, setPreview] = useState<{ order_count: number; total_amount: number } | null>(null);
  const [detail, setDetail] = useState<StatementDetail | null>(null);
  // payment
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
    try {
      const r = await getReceivables({ token: accessToken, organizationId: activeOrganizationId });
      setRows(r.clinics);
      setTotals({ out: r.total_outstanding, unbilled: r.total_unbilled });
    } catch (err) {
      setError(normalizeApiError(err));
    }
  }, [accessToken, activeOrganizationId]);

  const loadClinic = useCallback(
    async (id: string) => {
      if (!accessToken) return;
      const d = await getClinicBilling({ token: accessToken, organizationId: activeOrganizationId }, id);
      setData(d);
      setDisc(String(d.settings.default_discount_pct));
      setTerms(String(d.settings.payment_terms_days));
    },
    [accessToken, activeOrganizationId],
  );

  useEffect(() => {
    const timer = setTimeout(() => void loadList(), 0);
    return () => clearTimeout(timer);
  }, [loadList]);

  // Deep link from the clinic list: /app/admin/clinic-billing?clinic=<id>
  const deepLinked = useRef(false);
  useEffect(() => {
    if (!accessToken || deepLinked.current) return;
    const id = new URLSearchParams(window.location.search).get("clinic");
    deepLinked.current = true;
    if (id) {
      const timer = setTimeout(() => void openClinic(id), 0);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  async function openClinic(id: string) {
    setOrgId(id);
    setTab("overview");
    setDetail(null);
    setPreview(null);
    await guard(() => loadClinic(id));
  }

  async function refresh() {
    if (orgId) await loadClinic(orgId);
    await loadList();
  }

  async function searchPrices() {
    if (!ctx || !orgId) return;
    await guard(async () => {
      setPrices(await listClinicPrices(ctx, orgId, pq.trim(), onlyCustom));
      setPriceEdit({});
    });
  }

  const period = ps && pe ? { period_start: ps, period_end: pe } : null;

  return (
    <AppShell title="Hợp đồng và công nợ phòng khám" workspacePath="/app/admin">
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Hợp đồng, giá riêng và công nợ phòng khám</h1>
          <p className="text-sm text-slate-600">
            Lưu hợp đồng, đặt giá riêng cho từng phòng khám, chốt kết toán theo kỳ và theo dõi công nợ.
          </p>
        </div>
        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        {notice ? <p className="rounded-lg bg-green-50 p-2 text-sm text-green-800">{notice}</p> : null}

        {!orgId ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div className="rounded-xl border border-slate-200 bg-white p-3">
                <p className="text-xs text-slate-500">Tổng phải thu (đã kết toán)</p>
                <p className="text-lg font-semibold">{formatVnd(totals.out)}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-3">
                <p className="text-xs text-slate-500">Chưa kết toán</p>
                <p className="text-lg font-semibold">{formatVnd(totals.unbilled)}</p>
              </div>
            </div>
            {rows.length === 0 ? <p className="text-sm text-slate-500">Chưa có phòng khám nào trong hệ thống.</p> : null}
            <ul className="space-y-2">
              {rows.map((r) => (
                <li key={r.organization_id} className="rounded-xl border border-slate-200 bg-white p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-medium">{r.organization_name}</p>
                    <Button size="sm" onClick={() => void openClinic(r.organization_id)}>Mở</Button>
                  </div>
                  <p className="text-sm text-slate-600">
                    {r.has_activity
                      ? `Phải thu ${formatVnd(r.outstanding)} · chưa kết toán ${formatVnd(r.unbilled_amount)} (${r.unbilled_orders} đơn)`
                      : "Chưa có đơn nào. Anh vẫn có thể đính kèm hợp đồng và đặt giá riêng trước."}
                  </p>
                  {r.aging.d1_30 + r.aging.d31_60 + r.aging.d60_plus > 0 ? (
                    <p className="text-xs text-red-700">
                      Quá hạn {formatVnd(r.aging.d1_30 + r.aging.d31_60 + r.aging.d60_plus)}
                    </p>
                  ) : null}
                </li>
              ))}
            </ul>
            <p className="text-xs text-slate-500">
              Mở từng phòng khám để đính kèm hợp đồng, đặt giá riêng, chốt kết toán và theo dõi công nợ.
            </p>
          </div>
        ) : !data ? (
          <p className="text-sm text-slate-500">Đang tải…</p>
        ) : (
          <div className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => { setOrgId(null); setData(null); void loadList(); }}>
                ← Danh sách
              </Button>
              <p className="font-semibold">{data.clinic.name}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {TABS.map((t) => (
                <Button key={t.key} size="sm" variant={t.key === tab ? "primary" : "outline"} onClick={() => setTab(t.key)}>
                  {t.label}
                </Button>
              ))}
            </div>

            {tab === "overview" ? (
              <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
                <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                  {[
                    ["Đã kết toán", data.summary.billed],
                    ["Đã thanh toán", data.summary.paid],
                    ["Còn phải thu", data.summary.outstanding],
                    ["Chưa kết toán", data.summary.unbilled_amount],
                  ].map(([l, v]) => (
                    <div key={String(l)} className="rounded-lg bg-slate-50 p-2">
                      <p className="text-xs text-slate-500">{l}</p>
                      <p className="text-sm font-semibold">{formatVnd(Number(v))}</p>
                    </div>
                  ))}
                </div>
                <AgingRow aging={data.summary.aging} />
                <div className="border-t pt-3">
                  <p className="mb-2 text-sm font-medium">Điều khoản chung</p>
                  <div className="flex flex-wrap items-end gap-3 text-sm">
                    <label>
                      Chiết khấu mặc định (%)
                      <input type="number" min={0} max={100} value={disc} onChange={(e) => setDisc(e.target.value)} className={`${INPUT} ml-2 w-24`} />
                    </label>
                    <label>
                      Hạn thanh toán (ngày)
                      <input type="number" min={0} max={365} value={terms} onChange={(e) => setTerms(e.target.value)} className={`${INPUT} ml-2 w-24`} />
                    </label>
                    <Button
                      size="sm"
                      disabled={busy || !ctx || !orgId}
                      onClick={() =>
                        ctx && orgId &&
                        void guard(async () => {
                          await saveSettings(ctx, orgId, { default_discount_pct: Number(disc || 0), payment_terms_days: Number(terms || 0) });
                          await refresh();
                        }, "Đã lưu điều khoản.")
                      }
                    >
                      Lưu
                    </Button>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    Giá riêng từng xét nghiệm (tab Bảng giá, hiện {data.price_count} mục) được ưu tiên; xét nghiệm không có giá riêng sẽ trừ chiết khấu mặc định.
                    Giá chỉ áp dụng cho đơn mới tạo từ phiếu phòng khám hoặc chọn phòng khám khi tạo đơn.
                  </p>
                </div>
              </div>
            ) : null}

            {tab === "contracts" ? (
              <div className="space-y-3">
                <form
                  className="space-y-2 rounded-xl border border-slate-200 bg-white p-4"
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!ctx || !orgId) return;
                    const form = new FormData(e.currentTarget);
                    const el = e.currentTarget;
                    void guard(async () => {
                      await uploadContract(ctx, orgId, form);
                      el.reset();
                      await refresh();
                    }, "Đã lưu hợp đồng.");
                  }}
                >
                  <p className="text-sm font-medium">Thêm hợp đồng</p>
                  <div className="flex flex-wrap gap-2 text-sm">
                    <input name="title" required placeholder="Tên hợp đồng" aria-label="Tên hợp đồng" className={`${INPUT} min-w-60 flex-1`} />
                    <input name="contract_no" placeholder="Số hợp đồng" aria-label="Số hợp đồng" className={INPUT} />
                  </div>
                  <div className="flex flex-wrap gap-3 text-sm">
                    <label>Ngày ký <input name="signed_date" type="date" className={INPUT} /></label>
                    <label>Hiệu lực từ <input name="start_date" type="date" className={INPUT} /></label>
                    <label>đến <input name="end_date" type="date" className={INPUT} /></label>
                  </div>
                  <input name="note" placeholder="Ghi chú" aria-label="Ghi chú" className={`${INPUT} w-full`} />
                  <input name="file" type="file" accept=".pdf,.jpg,.jpeg,.png" aria-label="File hợp đồng" className="text-sm" />
                  <p className="text-xs text-slate-500">File PDF hoặc ảnh JPG/PNG, tối đa 10MB.</p>
                  <Button type="submit" size="sm" disabled={busy}>Lưu hợp đồng</Button>
                </form>
                {data.contracts.length === 0 ? <p className="text-sm text-slate-500">Chưa có hợp đồng nào.</p> : null}
                <ul className="space-y-2">
                  {data.contracts.map((c) => (
                    <li key={c.id} className="rounded-xl border border-slate-200 bg-white p-3">
                      <p className="font-medium">{c.title}{c.contract_no ? ` · ${c.contract_no}` : ""}</p>
                      <p className="text-sm text-slate-600">
                        Ký {c.signed_date ?? "—"} · hiệu lực {c.start_date ?? "—"} → {c.end_date ?? "không thời hạn"}
                      </p>
                      {c.note ? <p className="text-xs text-slate-500">{c.note}</p> : null}
                      {c.has_file && ctx && orgId ? (
                        <Button size="sm" variant="outline" className="mt-2" disabled={busy} onClick={() => void guard(() => downloadContract(ctx, orgId, c))}>
                          Tải {c.file_name ?? "file"}
                        </Button>
                      ) : (
                        <p className="mt-1 text-xs text-amber-700">Chưa đính kèm file</p>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {tab === "prices" ? (
              <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    value={pq}
                    onChange={(e) => setPq(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && void searchPrices()}
                    placeholder="Mã hoặc tên xét nghiệm"
                    aria-label="Tìm xét nghiệm"
                    className={`${INPUT} flex-1`}
                  />
                  <label className="flex items-center gap-1 text-sm">
                    <input type="checkbox" checked={onlyCustom} onChange={(e) => setOnlyCustom(e.target.checked)} /> Chỉ giá riêng
                  </label>
                  <Button size="sm" disabled={busy} onClick={() => void searchPrices()}>Tìm</Button>
                </div>
                <ul className="space-y-2">
                  {prices.map((p) => (
                    <li key={p.id} className="flex flex-wrap items-center gap-2 text-sm">
                      <span className="min-w-48 flex-1">{p.name} ({p.code}) · giá niêm yết {formatVnd(p.list_price)}</span>
                      <input
                        type="number"
                        min={0}
                        value={priceEdit[p.id] ?? (p.clinic_price ?? "")}
                        onChange={(e) => setPriceEdit((s) => ({ ...s, [p.id]: e.target.value }))}
                        placeholder="Giá riêng"
                        aria-label={`Giá riêng ${p.code}`}
                        className={`${INPUT} w-32`}
                      />
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={busy}
                        onClick={() =>
                          ctx && orgId &&
                          void guard(async () => {
                            const raw = priceEdit[p.id] ?? String(p.clinic_price ?? "");
                            await setClinicPrice(ctx, orgId, p.id, raw === "" ? null : Number(raw));
                            await searchPrices();
                            await refresh();
                          }, `Đã lưu giá ${p.code}.`)
                        }
                      >
                        Lưu
                      </Button>
                    </li>
                  ))}
                </ul>
                <p className="text-xs text-slate-500">Để trống rồi bấm Lưu để xóa giá riêng (quay về giá niêm yết trừ chiết khấu mặc định).</p>
              </div>
            ) : null}

            {tab === "statements" ? (
              <div className="space-y-3">
                <div className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
                  <p className="text-sm font-medium">Chốt kết toán một kỳ</p>
                  <div className="flex flex-wrap items-end gap-3 text-sm">
                    <label>Từ ngày <input type="date" value={ps} onChange={(e) => { setPs(e.target.value); setPreview(null); }} className={INPUT} /></label>
                    <label>Đến ngày <input type="date" value={pe} onChange={(e) => { setPe(e.target.value); setPreview(null); }} className={INPUT} /></label>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={busy || !period}
                      onClick={() => ctx && orgId && period && void guard(async () => setPreview(await previewStatement(ctx, orgId, period)))}
                    >
                      Xem trước
                    </Button>
                  </div>
                  {preview ? (
                    <div className="flex flex-wrap items-center gap-3 text-sm">
                      <span>{preview.order_count} đơn chưa kết toán · {formatVnd(preview.total_amount)}</span>
                      <Button
                        size="sm"
                        disabled={busy || preview.order_count === 0}
                        onClick={() =>
                          ctx && orgId && period &&
                          void guard(async () => {
                            await createStatement(ctx, orgId, period);
                            setPreview(null);
                            await refresh();
                          }, "Đã chốt kết toán.")
                        }
                      >
                        Chốt kết toán
                      </Button>
                    </div>
                  ) : null}
                  <p className="text-xs text-slate-500">Mỗi đơn chỉ thuộc một kỳ kết toán. Đơn đã hủy không được tính.</p>
                </div>
                {data.statements.length === 0 ? <p className="text-sm text-slate-500">Chưa có kỳ kết toán nào.</p> : null}
                <ul className="space-y-2">
                  {data.statements.map((s) => (
                    <li key={s.id} className="rounded-xl border border-slate-200 bg-white p-3">
                      <p className="font-medium">{s.statement_no}</p>
                      <p className="text-sm text-slate-600">
                        Kỳ {s.period_start} → {s.period_end} · {s.order_count} đơn · {formatVnd(s.total_amount)} · hạn {s.due_date}
                      </p>
                      <p className="text-sm">
                        Đã trả {formatVnd(s.paid)} ·{" "}
                        <span className={s.outstanding > 0 ? "font-medium text-red-700" : "text-green-700"}>
                          {s.outstanding > 0 ? `còn ${formatVnd(s.outstanding)}` : "đã thanh toán đủ"}
                        </span>
                      </p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <Button size="sm" variant="outline" disabled={busy} onClick={() => ctx && orgId && void guard(async () => setDetail(await getStatement(ctx, orgId, s.id)))}>
                          Xem chi tiết
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={busy}
                          onClick={() =>
                            ctx && orgId && window.confirm(`Hủy bảng kết toán ${s.statement_no}? Các đơn sẽ trở về trạng thái chưa kết toán.`) &&
                            void guard(async () => {
                              await voidStatement(ctx, orgId, s.id);
                              setDetail(null);
                              await refresh();
                            }, "Đã hủy bảng kết toán.")
                          }
                        >
                          Hủy
                        </Button>
                      </div>
                    </li>
                  ))}
                </ul>
                {detail ? (
                  <div className="space-y-2 rounded-xl border border-slate-300 bg-white p-4">
                    <p className="font-semibold">{detail.statement_no} · {detail.clinic_name}</p>
                    <p className="text-sm text-slate-600">Kỳ {detail.period_start} → {detail.period_end} · hạn thanh toán {detail.due_date}</p>
                    <table className="w-full text-left text-sm">
                      <thead>
                        <tr className="border-b text-xs text-slate-500">
                          <th className="py-1">Mã đơn</th>
                          <th>Bệnh nhân</th>
                          <th className="text-right">Số tiền</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.lines.map((l) => (
                          <tr key={l.order_code} className="border-b border-slate-100">
                            <td className="py-1">{l.order_code}</td>
                            <td>{l.patient_name}</td>
                            <td className="text-right">{formatVnd(l.amount)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    <p className="text-right font-semibold">Tổng: {formatVnd(detail.total_amount)}</p>
                    <Button size="sm" variant="outline" onClick={() => window.print()}>In / lưu PDF</Button>
                  </div>
                ) : null}
              </div>
            ) : null}

            {tab === "payments" ? (
              <div className="space-y-3">
                <div className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
                  <p className="text-sm font-medium">Ghi nhận thanh toán của phòng khám</p>
                  <div className="flex flex-wrap items-end gap-2 text-sm">
                    <input type="number" min={0} value={payAmount} onChange={(e) => setPayAmount(e.target.value)} placeholder="Số tiền" aria-label="Số tiền" className={`${INPUT} w-40`} />
                    <input type="date" value={payDate} onChange={(e) => setPayDate(e.target.value)} aria-label="Ngày thanh toán" className={INPUT} />
                    <input value={payMethod} onChange={(e) => setPayMethod(e.target.value)} placeholder="Hình thức (chuyển khoản…)" aria-label="Hình thức" className={INPUT} />
                    <input value={payRef} onChange={(e) => setPayRef(e.target.value)} placeholder="Nội dung / mã giao dịch" aria-label="Mã giao dịch" className={INPUT} />
                    <Button
                      size="sm"
                      disabled={busy || !(Number(payAmount) > 0)}
                      onClick={() =>
                        ctx && orgId &&
                        void guard(async () => {
                          await addPayment(ctx, orgId, { amount: Number(payAmount), paid_at: payDate || undefined, method: payMethod, reference: payRef });
                          setPayAmount("");
                          setPayRef("");
                          await refresh();
                        }, "Đã ghi nhận thanh toán.")
                      }
                    >
                      Ghi nhận
                    </Button>
                  </div>
                  <p className="text-xs text-slate-500">Tiền thu được trừ vào kỳ kết toán cũ nhất trước.</p>
                </div>
                {data.payments.length === 0 ? <p className="text-sm text-slate-500">Chưa có khoản thanh toán nào.</p> : null}
                <ul className="space-y-1">
                  {data.payments.map((p) => (
                    <li key={p.id} className="rounded-lg border border-slate-200 bg-white p-2 text-sm">
                      {p.paid_at} · <span className="font-medium">{formatVnd(p.amount)}</span>
                      {p.method ? ` · ${p.method}` : ""}
                      {p.reference ? ` · ${p.reference}` : ""}
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
