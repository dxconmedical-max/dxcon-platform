"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { fetchPublicResult, type PublicResult } from "@/lib/api/resultLinks";

function flagClass(flag: string | null): string {
  const f = (flag ?? "").toUpperCase();
  if (f === "" || f === "NORMAL") return "";
  return "font-semibold text-red-600";
}

export default function PublicResultPage() {
  const params = useParams<{ token: string }>();
  const token = params?.token ?? "";
  const [data, setData] = useState<PublicResult | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    fetchPublicResult(token)
      .then((r) => {
        if (!cancelled) setData(r);
      })
      .catch(() => {
        if (!cancelled) setFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <main className="mx-auto max-w-2xl px-4 py-8 text-slate-900">
      <h1 className="text-xl font-semibold">Kết quả xét nghiệm</h1>
      {failed ? (
        <p className="mt-6 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm">
          Link không hợp lệ hoặc đã hết hạn. Vui lòng liên hệ nơi lấy mẫu để được cấp link mới.
        </p>
      ) : !data ? (
        <p className="mt-6 text-sm text-slate-500">Đang tải…</p>
      ) : (
        <>
          <dl className="mt-4 grid grid-cols-2 gap-2 text-sm">
            <dt className="text-slate-500">Họ tên</dt>
            <dd>{data.patient_name}</dd>
            <dt className="text-slate-500">Mã đơn</dt>
            <dd className="font-mono text-xs">{data.order_code}</dd>
            <dt className="text-slate-500">Ngày có kết quả</dt>
            <dd>
              {new Date(data.released_at).toLocaleString("vi-VN", { timeZone: "Asia/Ho_Chi_Minh" })}
            </dd>
          </dl>
          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-slate-500">
                <tr>
                  <th className="py-2 pr-3">Xét nghiệm</th>
                  <th className="py-2 pr-3">Kết quả</th>
                  <th className="py-2 pr-3">Đơn vị</th>
                  <th className="py-2">Tham chiếu</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((i, idx) => (
                  <tr key={`${i.test_name}-${idx}`} className="border-t border-slate-200">
                    <td className="py-2 pr-3">{i.test_name}</td>
                    <td className={`py-2 pr-3 ${flagClass(i.flag)}`}>{i.result_value ?? "—"}</td>
                    <td className="py-2 pr-3">{i.unit ?? ""}</td>
                    <td className="py-2">{i.reference_range ?? ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-6 text-xs text-slate-500">
            Kết quả chỉ có giá trị tham khảo và cần được bác sĩ giải thích. Không chia sẻ link này cho người khác. Link
            tự hết hạn sau 30 ngày.
          </p>
        </>
      )}
    </main>
  );
}
