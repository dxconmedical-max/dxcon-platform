import { AppShell } from "@/components/layout/AppShell";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import Link from "next/link";

export function IntegrationHub({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <AppShell title={title} workspacePath="/app/admin">
      <div className="space-y-6">
        <section className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="text-2xl font-semibold text-slate-900">{title}</h2>
          <p className="mt-2 text-slate-600">{subtitle}</p>
        </section>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[
            ["/app/admin/integrations/connectors", "Connectors", "LIS, HIS, EMR, PACS and custom API connectors"],
            ["/app/admin/integrations/messages", "Messages", "Tin nhắn tích hợp đến và đi"],
            ["/app/admin/integrations/exceptions", "Exceptions", "Tin nhắn lỗi và hàng đợi lỗi"],
            ["/app/admin/integrations/mappings", "Mappings", "Quy tắc ánh xạ trường và mã xét nghiệm"],
            ["/app/admin/integrations/webhooks", "Webhooks", "Đăng ký sự kiện và lượt gửi"],
            ["/app/admin/integrations/health", "Health", "Tình trạng kết nối và lưu lượng"],
          ].map(([href, label, desc]) => (
            <Card key={href}>
              <CardTitle>{label}</CardTitle>
              <CardDescription>{desc}</CardDescription>
              <Link href={href} className="mt-4 inline-block text-sm font-medium text-teal-700">
                Mở
              </Link>
            </Card>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
