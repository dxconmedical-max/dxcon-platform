import type { JobInfo } from "@/lib/api/sampleCollection";

const money = (n: number | null | undefined) =>
  n == null ? "—" : `${Math.round(n).toLocaleString("vi-VN")} ₫`;

function age(dob: string | null | undefined): string {
  if (!dob) return "";
  const d = new Date(dob);
  if (Number.isNaN(d.getTime())) return dob;
  const years = Math.floor((Date.now() - d.getTime()) / (365.25 * 24 * 3600 * 1000));
  return `${years} tuổi`;
}

export function JobInfoCard({ info }: { info?: JobInfo }) {
  if (!info) return null;
  if (!info.order_found) {
    return (
      <p className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
        Không tìm thấy đơn của yêu cầu này (có thể đã bị xóa). Liên hệ tiếp nhận trước khi đi lấy mẫu.
        {info.patient_phone ? ` SĐT liên hệ: ${info.patient_phone}.` : ""}
      </p>
    );
  }
  const who = [info.patient_gender, age(info.patient_dob)].filter(Boolean).join(" · ");
  return (
    <div className="space-y-3 rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm">
      <div>
        <div className="font-medium">
          {info.patient_name ?? "—"} {who ? <span className="font-normal text-slate-500">({who})</span> : null}
        </div>
        <div className="text-slate-600">
          {info.patient_phone ? (
            <a className="text-sky-700 underline" href={`tel:${info.patient_phone}`}>
              {info.patient_phone}
            </a>
          ) : (
            "Chưa có SĐT"
          )}
          {info.address ? ` · ${info.address}` : ""}
        </div>
      </div>
      <div>
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Xét nghiệm</div>
        {info.tests.length === 0 ? (
          <p className="text-slate-500">Chưa có xét nghiệm.</p>
        ) : (
          <ul className="mt-1 space-y-0.5">
            {info.tests.map((t, i) => (
              <li key={`${t.test_code}-${i}`} className="flex justify-between gap-3">
                <span>
                  {t.test_name}
                  {t.quantity && t.quantity > 1 ? ` ×${t.quantity}` : ""}
                </span>
                <span className="text-slate-600">{money(t.line_total)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="flex flex-wrap gap-x-6 gap-y-1 border-t border-slate-200 pt-2">
        <span>Tổng: <b>{money(info.total_amount)}</b></span>
        <span>Đã thu: {money(info.paid_amount)}</span>
        <span className={info.due_amount ? "font-semibold text-red-600" : "text-emerald-700"}>
          Còn thu: {money(info.due_amount)}
        </span>
      </div>
      {info.note ? <p className="text-slate-700">Ghi chú: {info.note}</p> : null}
    </div>
  );
}
