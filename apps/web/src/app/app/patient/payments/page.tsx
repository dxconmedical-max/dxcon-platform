import { AppShell } from "@/components/layout/AppShell";

export const metadata = { title: "Thanh toán" };

export default function PatientPaymentsPage() {
  return (
    <AppShell title="Thanh toán" workspacePath="/app/patient">
      <div className="max-w-xl space-y-3 text-sm text-slate-700">
        <p>
          Hiện thanh toán được thực hiện trực tiếp khi lấy mẫu hoặc tại quầy tiếp nhận. Biên nhận được nhân viên in và
          đưa cho bạn ngay sau khi thu tiền.
        </p>
        <p>
          Kết quả xét nghiệm được gửi qua link hoặc mã QR riêng cho từng đơn. Hãy quét mã QR trên phiếu kết quả để xem.
        </p>
        <p className="text-slate-500">Thanh toán trực tuyến sẽ được bổ sung sau.</p>
      </div>
    </AppShell>
  );
}
