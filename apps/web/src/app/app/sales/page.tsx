"use client";

import { useCallback, useEffect, useState } from "react";

import { MiniBars } from "@/components/charts/MiniBars";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import { formatVnd } from "@/lib/format";
import {
  addActivity,
  createAccount,
  getAccount,
  KIND_LABELS,
  listAccounts,
  listSales,
  setSaleTarget,
  STAGE_LABELS,
  STAGES,
  TYPE_LABELS,
  updateAccount,
  type CrmAccount,
  type CrmDetail,
  type CrmList,
  type SaleRow,
  downloadAccountsExcel,
  downloadImportTemplate,
  importAccounts,
  type ImportResult,
} from "@/lib/api/crm";
import { searchOrganizations, type OrgHit } from "@/lib/api/labPayables";

const INPUT = "rounded-lg border border-slate-300 px-3 py-1.5 text-sm";

function thisMonth(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

export default function SalesCrmPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = accessToken ? { token: accessToken, organizationId: activeOrganizationId } : null;
  const [month, setMonth] = useState(thisMonth());
  const [stage, setStage] = useState("");
  const [q, setQ] = useState("");
  const [data, setData] = useState<CrmList | null>(null);
  const [sales, setSales] = useState<SaleRow[]>([]);
  const [view, setView] = useState<"accounts" | "team">("accounts");
  const [selected, setSelected] = useState<CrmDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const [form, setForm] = useState({ name: "", account_type: "CLINIC", phone: "", contact_person: "", district: "", est_monthly_cases: "", owner_user_id: "" });
  const [edit, setEdit] = useState({ est_monthly_cases: "", next_followup_date: "", notes: "" });
  const [actKind, setActKind] = useState("CALL");
  const [actText, setActText] = useState("");
  const [actNext, setActNext] = useState("");
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [orgQ, setOrgQ] = useState("");
  const [orgHits, setOrgHits] = useState<OrgHit[]>([]);
  const [targets, setTargets] = useState<Record<string, { cases: string; revenue: string }>>({});

  const isAdmin = data?.is_admin ?? false;

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

  const load = useCallback(async () => {
    if (!accessToken) return;
    const c = { token: accessToken, organizationId: activeOrganizationId };
    try {
      const d = await listAccounts(c, month, stage, q.trim());
      setData(d);
      if (d.is_admin) setSales((await listSales(c, month)).sales);
    } catch (err) {
      setError(normalizeApiError(err));
    }
  }, [accessToken, activeOrganizationId, month, stage, q]);

  useEffect(() => {
    const timer = setTimeout(() => void load(), 0);
    return () => clearTimeout(timer);
  }, [load]);

  async function open(id: string) {
    if (!ctx) return;
    await guard(async () => {
      const d = await getAccount(ctx, id);
      setSelected(d);
      setEdit({
        est_monthly_cases: String(d.account.est_monthly_cases || ""),
        next_followup_date: d.account.next_followup_date ?? "",
        notes: d.account.notes ?? "",
      });
      setOrgHits([]);
    });
  }

  async function reloadSelected() {
    if (selected && ctx) setSelected(await getAccount(ctx, selected.account.id));
    await load();
  }

  const acc: CrmAccount | null = selected?.account ?? null;

  return (
    <AppShell title="Khách hàng (CRM)" workspacePath="/app/sales">
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Khách hàng và đội Sale</h1>
          <p className="text-sm text-slate-600">
            {isAdmin
              ? "Theo dõi khách hàng, chăm sóc, chỉ tiêu Sale và thị phần (số ca thực nhận so với ước tính mỗi tháng)."
              : "Khách hàng của bạn: ghi nhật ký chăm sóc, hẹn lần liên hệ tiếp theo và xem số ca thực nhận so với ước tính."}
          </p>
        </div>
        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        {notice ? <p className="rounded-lg bg-green-50 p-2 text-sm text-green-800">{notice}</p> : null}

        <div className="flex flex-wrap items-end gap-2">
          <label className="text-xs">
            Tháng
            <input type="month" value={month} onChange={(e) => setMonth(e.target.value)} className={`${INPUT} block`} />
          </label>
          <Button size="sm" variant="outline" disabled={busy || !ctx} onClick={() => ctx && void guard(async () => downloadAccountsExcel(ctx, month))}>
            Xuất Excel
          </Button>
          {isAdmin ? (
            <div className="flex gap-2">
              {(["accounts", "team"] as const).map((v) => (
                <button key={v} type="button" onClick={() => setView(v)} className={`rounded-full px-3 py-1 text-sm ${view === v ? "bg-slate-900 text-white" : "bg-slate-100"}`}>
                  {v === "accounts" ? "Khách hàng" : "Đội Sale"}
                </button>
              ))}
            </div>
          ) : null}
        </div>

        {data ? (
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            {[
              ["Khách hàng", String(data.totals.accounts)],
              ["Ước tính ca/tháng", String(data.totals.est_monthly_cases)],
              ["Ca thực nhận", String(data.totals.cases)],
              ["Thị phần (thực nhận / ước tính)", data.totals.share_pct === null ? "—" : `${data.totals.share_pct}%`],
              ["Doanh thu", formatVnd(data.totals.revenue)],
              ...(isAdmin ? [["Lãi", formatVnd(data.totals.margin ?? 0)]] : []),
              ["Quá hạn chăm sóc", String(data.totals.overdue_followups)],
              ["Khách đang gửi nhưng im >30 ngày", String(data.totals.quiet_accounts)],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xl border border-slate-200 bg-white p-3">
                <p className="text-xs text-slate-500">{label}</p>
                <p className="text-sm font-semibold">{value}</p>
              </div>
            ))}
          </div>
        ) : null}

        {view === "team" && isAdmin ? (
          <section className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="font-medium">Đội Sale tháng {month}</h2>
            {sales.length === 0 ? <p className="text-sm text-slate-500">Chưa có tài khoản Sale. Tạo ở Quản trị → Tài khoản nhân viên, vai trò “Sale (kinh doanh)”.</p> : null}
            <ul className="space-y-3">
              {sales.map((s) => {
                const t = targets[s.user_id] ?? { cases: String(s.target_cases || ""), revenue: String(s.target_revenue || "") };
                return (
                  <li key={s.user_id} className="rounded-lg border border-slate-200 p-3 text-sm">
                    <p className="font-medium">{s.email}</p>
                    <p className="text-xs text-slate-600">
                      {s.accounts} khách ({s.active_accounts} đang gửi mẫu) · {s.cases} ca{s.cases_pct !== null ? ` (${s.cases_pct}% chỉ tiêu)` : ""} · doanh thu {formatVnd(s.revenue)}
                      {s.revenue_pct !== null ? ` (${s.revenue_pct}% chỉ tiêu)` : ""} · lãi {formatVnd(s.margin)}
                    </p>
                    <div className="mt-2 flex flex-wrap items-end gap-2">
                      <label className="text-xs">Chỉ tiêu số ca<input type="number" min={0} value={t.cases} onChange={(e) => setTargets({ ...targets, [s.user_id]: { ...t, cases: e.target.value } })} className={`${INPUT} block w-28`} /></label>
                      <label className="text-xs">Chỉ tiêu doanh thu<input type="number" min={0} value={t.revenue} onChange={(e) => setTargets({ ...targets, [s.user_id]: { ...t, revenue: e.target.value } })} className={`${INPUT} block w-40`} /></label>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={busy}
                        onClick={() => ctx && void guard(async () => { await setSaleTarget(ctx, s.user_id, { month, target_cases: Number(t.cases || 0), target_revenue: Number(t.revenue || 0) }); await load(); }, "Đã lưu chỉ tiêu.")}
                      >
                        Lưu chỉ tiêu
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>
        ) : (
          <>
            <section className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="font-medium">Thêm khách hàng</h2>
              <div className="grid gap-2 sm:grid-cols-3">
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Tên phòng khám / bệnh viện *" aria-label="Tên khách hàng" className={INPUT} />
                <select value={form.account_type} onChange={(e) => setForm({ ...form, account_type: e.target.value })} aria-label="Loại khách hàng" className={INPUT}>
                  {Object.entries(TYPE_LABELS).map(([k, v]) => (
                    <option key={k} value={k}>{v}</option>
                  ))}
                </select>
                <input value={form.contact_person} onChange={(e) => setForm({ ...form, contact_person: e.target.value })} placeholder="Người liên hệ" aria-label="Người liên hệ" className={INPUT} />
                <input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} placeholder="Điện thoại" aria-label="Điện thoại" className={INPUT} />
                <input value={form.district} onChange={(e) => setForm({ ...form, district: e.target.value })} placeholder="Quận / khu vực" aria-label="Quận" className={INPUT} />
                <input type="number" min={0} value={form.est_monthly_cases} onChange={(e) => setForm({ ...form, est_monthly_cases: e.target.value })} placeholder="Ước tính ca xét nghiệm / tháng" aria-label="Ước tính ca mỗi tháng" className={INPUT} />
                {isAdmin ? (
                  <select value={form.owner_user_id} onChange={(e) => setForm({ ...form, owner_user_id: e.target.value })} aria-label="Sale phụ trách" className={INPUT}>
                    <option value="">Chưa giao Sale</option>
                    {sales.map((s) => (
                      <option key={s.user_id} value={s.user_id}>{s.email}</option>
                    ))}
                  </select>
                ) : null}
              </div>
              <Button
                size="sm"
                disabled={busy || !form.name.trim()}
                onClick={() =>
                  ctx &&
                  void guard(async () => {
                    await createAccount(ctx, { ...form, est_monthly_cases: Number(form.est_monthly_cases || 0) });
                    setForm({ name: "", account_type: "CLINIC", phone: "", contact_person: "", district: "", est_monthly_cases: "", owner_user_id: "" });
                    await load();
                  }, "Đã thêm khách hàng.")
                }
              >
                Thêm
              </Button>
            </section>

            <section className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
              <h2 className="font-medium">Nhập nhiều khách hàng từ Excel</h2>
              <p className="text-xs text-slate-600">
                Tải biểu mẫu, điền mỗi dòng một khách hàng, rồi chọn file để kiểm tra trước. Khách trùng tên sẽ được bỏ qua.
                {isAdmin ? " Cột cuối là email Sale phụ trách (để trống nếu chưa giao)." : " Khách nhập vào sẽ thuộc về bạn."}
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <Button size="sm" variant="outline" disabled={busy || !ctx} onClick={() => ctx && void guard(async () => downloadImportTemplate(ctx))}>
                  Tải biểu mẫu
                </Button>
                <input
                  type="file"
                  accept=".xlsx,.csv,.tsv"
                  aria-label="Chọn file khách hàng"
                  onChange={(e) => {
                    setImportFile(e.target.files?.[0] ?? null);
                    setImportResult(null);
                  }}
                  className="text-sm"
                />
                <Button size="sm" disabled={busy || !ctx || !importFile} onClick={() => ctx && importFile && void guard(async () => setImportResult(await importAccounts(ctx, importFile, false)))}>
                  Kiểm tra file
                </Button>
              </div>
              {importResult ? (
                <div className="space-y-1 text-sm">
                  <p>
                    {importResult.applied ? "Đã thêm" : "Sẽ thêm"} <b>{importResult.created}</b> khách · bỏ qua {importResult.skipped_count} trùng · {importResult.error_count} dòng lỗi.
                  </p>
                  {importResult.errors.map((e) => (
                    <p key={`e${e.row}`} className="text-xs text-red-700">Dòng {e.row}: {e.error}</p>
                  ))}
                  {importResult.skipped.map((k) => (
                    <p key={`s${k.row}`} className="text-xs text-slate-500">Dòng {k.row} ({k.name}): {k.reason}</p>
                  ))}
                  {!importResult.applied && importResult.created > 0 && ctx && importFile ? (
                    <Button
                      size="sm"
                      disabled={busy}
                      onClick={() =>
                        void guard(async () => {
                          setImportResult(await importAccounts(ctx, importFile, true));
                          await load();
                        })
                      }
                    >
                      Nhập {importResult.created} khách hợp lệ
                    </Button>
                  ) : null}
                </div>
              ) : null}
            </section>

            <section className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
              <div className="flex flex-wrap items-center gap-2">
                <button type="button" onClick={() => setStage("")} className={`rounded-full px-3 py-1 text-xs ${stage === "" ? "bg-slate-900 text-white" : "bg-slate-100"}`}>
                  Tất cả
                </button>
                {STAGES.map((s) => (
                  <button key={s} type="button" onClick={() => setStage(s)} className={`rounded-full px-3 py-1 text-xs ${stage === s ? "bg-slate-900 text-white" : "bg-slate-100"}`}>
                    {STAGE_LABELS[s]} ({data?.stage_counts[s] ?? 0})
                  </button>
                ))}
                <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm theo tên" aria-label="Tìm khách hàng" className={`${INPUT} ml-auto w-44`} />
              </div>
              {data && data.accounts.length === 0 ? <p className="text-sm text-slate-500">Chưa có khách hàng nào.</p> : null}
              <ul className="space-y-2">
                {data?.accounts.map((a) => (
                  <li key={a.id} className="rounded-lg border border-slate-200 p-3 text-sm">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="font-medium">{a.name} <span className="text-xs text-slate-500">· {TYPE_LABELS[a.account_type] ?? a.account_type}{a.district ? ` · ${a.district}` : ""}</span></p>
                        <p className="text-xs text-slate-600">
                          {STAGE_LABELS[a.stage]}
                          {isAdmin ? ` · Sale: ${a.owner_name ?? "chưa giao"}` : ""}
                          {a.organization_id ? ` · ${a.cases} ca / ước tính ${a.est_monthly_cases}${a.share_pct !== null ? ` (${a.share_pct}%)` : ""}` : ` · ước tính ${a.est_monthly_cases} ca/tháng (chưa liên kết đơn vị)`}
                        </p>
                        {a.stage === "ACTIVE" && (a.days_quiet === null || a.days_quiet > 30) ? (
                          <p className="text-xs text-amber-700">{a.days_quiet === null ? "Chưa có ca nào" : `${a.days_quiet} ngày chưa gửi mẫu`}</p>
                        ) : null}
                        {a.next_followup_date ? (
                          <p className={`text-xs ${a.followup_overdue ? "text-red-700" : "text-slate-500"}`}>
                            Hẹn chăm sóc: {a.next_followup_date}{a.followup_overdue ? " (quá hạn)" : ""}
                          </p>
                        ) : null}
                      </div>
                      <Button size="sm" variant="outline" onClick={() => void open(a.id)}>Mở</Button>
                    </div>
                  </li>
                ))}
              </ul>
            </section>

            {acc ? (
              <section className="space-y-3 rounded-xl border border-teal-200 bg-white p-4">
                <div className="flex items-center justify-between">
                  <h2 className="font-medium">{acc.name}</h2>
                  <Button size="sm" variant="outline" onClick={() => setSelected(null)}>Đóng</Button>
                </div>
                <div className="flex flex-wrap items-end gap-2">
                  <label className="text-xs">
                    Giai đoạn
                    <select
                      value={acc.stage}
                      disabled={busy}
                      onChange={(e) => ctx && void guard(async () => { await updateAccount(ctx, acc.id, { stage: e.target.value }); await reloadSelected(); }, "Đã đổi giai đoạn.")}
                      className={`${INPUT} block`}
                    >
                      {STAGES.map((s) => (
                        <option key={s} value={s}>{STAGE_LABELS[s]}</option>
                      ))}
                    </select>
                  </label>
                  <label className="text-xs">Ước tính ca/tháng<input type="number" min={0} value={edit.est_monthly_cases} onChange={(e) => setEdit({ ...edit, est_monthly_cases: e.target.value })} className={`${INPUT} block w-32`} /></label>
                  <label className="text-xs">Hẹn chăm sóc<input type="date" value={edit.next_followup_date} onChange={(e) => setEdit({ ...edit, next_followup_date: e.target.value })} className={`${INPUT} block`} /></label>
                </div>
                <label className="block text-xs">
                  Ghi chú
                  <textarea value={edit.notes} onChange={(e) => setEdit({ ...edit, notes: e.target.value })} rows={2} className={`${INPUT} block w-full`} />
                </label>
                <Button
                  size="sm"
                  disabled={busy}
                  onClick={() =>
                    ctx &&
                    void guard(async () => {
                      await updateAccount(ctx, acc.id, { est_monthly_cases: Number(edit.est_monthly_cases || 0), next_followup_date: edit.next_followup_date, notes: edit.notes });
                      await reloadSelected();
                    }, "Đã lưu.")
                  }
                >
                  Lưu thông tin
                </Button>

                {isAdmin ? (
                  <div className="space-y-2 rounded-lg bg-slate-50 p-3">
                    <label className="block text-xs">
                      Sale phụ trách
                      <select
                        value={acc.owner_user_id ?? ""}
                        disabled={busy}
                        onChange={(e) => ctx && void guard(async () => { await updateAccount(ctx, acc.id, { owner_user_id: e.target.value }); await reloadSelected(); }, "Đã giao Sale.")}
                        className={`${INPUT} block`}
                      >
                        <option value="">Chưa giao</option>
                        {sales.map((s) => (
                          <option key={s.user_id} value={s.user_id}>{s.email}</option>
                        ))}
                      </select>
                    </label>
                    <p className="text-xs text-slate-600">
                      {acc.organization_id ? "Đã liên kết với đơn vị trong hệ thống (số ca thực nhận lấy từ các đơn của đơn vị này)." : "Chưa liên kết. Liên kết với đơn vị trong hệ thống để tính số ca thực nhận."}
                    </p>
                    <div className="flex gap-2">
                      <input value={orgQ} onChange={(e) => setOrgQ(e.target.value)} placeholder="Tên hoặc mã đơn vị" aria-label="Tìm đơn vị để liên kết" className={`${INPUT} flex-1`} />
                      <Button size="sm" variant="outline" disabled={busy} onClick={() => ctx && void guard(async () => setOrgHits(await searchOrganizations(ctx, orgQ.trim())))}>Tìm</Button>
                    </div>
                    <ul className="space-y-1">
                      {orgHits.map((o) => (
                        <li key={o.id} className="flex items-center justify-between gap-2 text-sm">
                          <span>{o.name} <span className="text-xs text-slate-500">({o.code})</span></span>
                          <Button size="sm" disabled={busy} onClick={() => ctx && void guard(async () => { await updateAccount(ctx, acc.id, { organization_id: o.id }); setOrgHits([]); await reloadSelected(); }, "Đã liên kết.")}>Liên kết</Button>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {selected && selected.history.length ? (
                  <div>
                    <p className="text-sm font-medium">Số ca thực nhận 6 tháng gần nhất</p>
                    <MiniBars label="Số ca theo tháng" points={selected.history.map((h) => ({ label: h.month.slice(2), value: h.cases }))} />
                  </div>
                ) : null}

                <div className="space-y-2">
                  <p className="text-sm font-medium">Nhật ký chăm sóc</p>
                  <div className="flex flex-wrap items-end gap-2">
                    <select value={actKind} onChange={(e) => setActKind(e.target.value)} aria-label="Loại liên hệ" className={INPUT}>
                      {Object.entries(KIND_LABELS).map(([k, v]) => (
                        <option key={k} value={k}>{v}</option>
                      ))}
                    </select>
                    <input value={actText} onChange={(e) => setActText(e.target.value)} placeholder="Nội dung (đã nói gì, kết quả)" aria-label="Nội dung liên hệ" className={`${INPUT} min-w-60 flex-1`} />
                    <label className="text-xs">Hẹn lần sau<input type="date" value={actNext} onChange={(e) => setActNext(e.target.value)} className={`${INPUT} block`} /></label>
                    <Button
                      size="sm"
                      disabled={busy || !actText.trim()}
                      onClick={() =>
                        ctx &&
                        void guard(async () => {
                          await addActivity(ctx, acc.id, { kind: actKind, summary: actText, next_followup_date: actNext || undefined });
                          setActText("");
                          setActNext("");
                          await reloadSelected();
                        }, "Đã ghi nhật ký.")
                      }
                    >
                      Ghi
                    </Button>
                  </div>
                  <ul className="divide-y divide-slate-100 text-sm">
                    {selected?.activities.map((a) => (
                      <li key={a.id} className="py-2">
                        <p><span className="font-medium">{KIND_LABELS[a.kind] ?? a.kind}</span> · {a.summary}</p>
                        <p className="text-xs text-slate-500">{a.at?.slice(0, 16).replace("T", " ")} · {a.by ?? ""}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              </section>
            ) : null}
          </>
        )}
      </div>
    </AppShell>
  );
}
