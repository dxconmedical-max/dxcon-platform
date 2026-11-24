import type { CollectionRate, LabTat } from "@/lib/api/executive";

const hours = (v: number | null) => (v == null ? "—" : `${v} giờ`);

export function CollectionPanel({ data }: { data: CollectionRate }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4">
      <h2 className="mb-1 text-sm font-semibold">Tỷ lệ lấy mẫu</h2>
      <p className="mb-3 text-xs text-slate-500">
        Số ca đã lấy được trên tổng số ca đã giao (không tính ca hủy). Ca bị từ chối hoặc cần lấy lại tính là chưa đạt.
      </p>
      {data.total === 0 ? (
        <p className="text-sm text-slate-500">Chưa có ca lấy mẫu trong kỳ này.</p>
      ) : (
        <>
          <p className="text-2xl font-semibold">
            {data.rate_pct}% <span className="text-sm font-normal text-slate-500">({data.collected}/{data.total} ca)</span>
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Đang xử lý: {data.open} · Bị từ chối / lấy lại: {data.failed}
          </p>
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500">
                <th className="py-1">Nhân viên</th>
                <th className="py-1 text-right">Đã lấy</th>
                <th className="py-1 text-right">Tổng</th>
                <th className="py-1 text-right">Tỷ lệ</th>
              </tr>
            </thead>
            <tbody>
              {data.by_collector.map((c) => (
                <tr key={c.collector} className="border-t border-slate-100">
                  <td className="py-1">{c.collector}</td>
                  <td className="py-1 text-right">{c.collected}</td>
                  <td className="py-1 text-right">{c.total}</td>
                  <td className="py-1 text-right">{c.rate_pct == null ? "—" : `${c.rate_pct}%`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}

export function LabTatPanel({ data }: { data: LabTat[] }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4">
      <h2 className="mb-1 text-sm font-semibold">TAT từng phòng lab</h2>
      <p className="mb-3 text-xs text-slate-500">
        Xử lý: từ lúc vào hàng đợi lab đến lúc duyệt. Toàn trình: từ lúc tạo đơn đến lúc trả kết quả.
      </p>
      {data.length === 0 ? (
        <p className="text-sm text-slate-500">Chưa có đơn nào được duyệt trong kỳ này.</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="py-1">Phòng lab</th>
              <th className="py-1 text-right">Số đơn</th>
              <th className="py-1 text-right">Xử lý</th>
              <th className="py-1 text-right">Toàn trình</th>
            </tr>
          </thead>
          <tbody>
            {data.map((l) => (
              <tr key={l.laboratory} className="border-t border-slate-100">
                <td className="py-1">{l.laboratory}</td>
                <td className="py-1 text-right">{l.orders}</td>
                <td className="py-1 text-right">{hours(l.processing_hours_avg)}</td>
                <td className="py-1 text-right">{hours(l.end_to_end_hours_avg)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
