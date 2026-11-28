import { formatVnd } from "@/lib/format";
import type { ProfitRow } from "@/lib/api/labPayables";

const short = (v: number) => {
  const a = Math.abs(v);
  const s = a >= 1e9 ? `${(a / 1e9).toFixed(1)} tỷ` : a >= 1e6 ? `${(a / 1e6).toFixed(1)} tr` : a >= 1e3 ? `${Math.round(a / 1e3)}k` : String(Math.round(a));
  return v < 0 ? `-${s}` : s;
};

/** Revenue and margin per month. Values are always printed, never colour alone. */
export function MonthlyTrend({ rows }: { rows: ProfitRow[] }) {
  if (rows.length === 0) return <p className="text-sm text-slate-500">Chưa có số liệu.</p>;
  const max = Math.max(1, ...rows.map((r) => Math.max(r.sell, Math.abs(r.margin))));
  const h = (v: number) => `${Math.max(2, (Math.abs(v) / max) * 120)}px`;
  return (
    <div>
      <div role="img" aria-label="Doanh thu và lãi theo tháng" className="flex h-40 items-end gap-3 overflow-x-auto">
        {rows.map((r) => (
          <div key={r.label} className="flex min-w-14 flex-1 flex-col items-center justify-end gap-1">
            <div className="flex items-end gap-1">
              <div className="flex flex-col items-center">
                <span className="text-[10px] text-slate-500">{short(r.sell)}</span>
                <div className="w-4 rounded-t bg-slate-400" style={{ height: h(r.sell) }} />
              </div>
              <div className="flex flex-col items-center">
                <span className={`text-[10px] ${r.margin < 0 ? "text-red-700" : "text-teal-800"}`}>{short(r.margin)}</span>
                <div className={`w-4 rounded-t ${r.margin < 0 ? "bg-red-600" : "bg-teal-600"}`} style={{ height: h(r.margin) }} />
              </div>
            </div>
            <span className="text-[10px] text-slate-600">{r.label}</span>
          </div>
        ))}
      </div>
      <p className="mt-1 text-xs text-slate-500">
        <span className="mr-3">▇ xám: doanh thu</span>
        <span>▇ xanh: lãi</span>
      </p>
    </div>
  );
}

/** Horizontal ranking bars (top N) with the value and margin % written next to each bar. */
export function RankBars({ rows, valueOf, caption, limit = 8 }: { rows: ProfitRow[]; valueOf: (r: ProfitRow) => number; caption: (r: ProfitRow) => string; limit?: number }) {
  const top = [...rows].sort((a, b) => valueOf(b) - valueOf(a)).slice(0, limit);
  if (top.length === 0) return <p className="text-sm text-slate-500">Chưa có số liệu.</p>;
  const max = Math.max(1, ...top.map((r) => Math.abs(valueOf(r))));
  return (
    <ul className="space-y-1.5">
      {top.map((r) => (
        <li key={r.label} className="text-sm">
          <div className="flex justify-between gap-2">
            <span className="truncate">{r.label}</span>
            <span className="shrink-0 text-xs text-slate-600">{caption(r)}</span>
          </div>
          <div className="h-2 rounded bg-slate-100">
            <div
              className={`h-2 rounded ${valueOf(r) < 0 ? "bg-red-600" : "bg-teal-600"}`}
              style={{ width: `${Math.max(2, (Math.abs(valueOf(r)) / max) * 100)}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

export const moneyCaption = (r: ProfitRow) => `${formatVnd(r.margin)} · ${r.margin_pct}%`;
