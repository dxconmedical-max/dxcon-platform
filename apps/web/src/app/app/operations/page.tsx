import Link from "next/link";

import { AppShell } from "@/components/layout/AppShell";
import { PilotReadinessHub } from "@/components/pilot/PilotReadinessHub";

export const metadata = { title: "Operations" };

export default function OperationsPage() {
  return (
    <AppShell title="Operations" workspacePath="/app/operations">
      <div className="mb-4 flex flex-wrap gap-4 text-sm">
        <Link className="text-teal-700 underline" href="/app/operations/orders">
          Danh sách đơn &amp; báo cáo
        </Link>
        <Link className="text-teal-700 underline" href="/app/operations/collections">
          Lấy mẫu tại nhà &amp; gán người
        </Link>
        <Link className="text-teal-700 underline" href="/app/operations/report">
          Báo cáo doanh thu
        </Link>
        <Link className="text-teal-700 underline" href="/app/operations/live-map">
          Bản đồ người lấy mẫu
        </Link>
        <Link className="text-teal-700 underline" href="/app/support">
          Phiếu hỗ trợ
        </Link>
      </div>
      <PilotReadinessHub
        title="Operations dashboard"
        subtitle="Today's orders, incidents, collectors, and SLA signals from the operations center."
        endpoint="/api/v1/pilot-readiness/operations-dashboard"
      />
    </AppShell>
  );
}
