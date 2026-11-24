"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { API_BASE_URL } from "@/lib/constants";

export default function PartnerRegisterPage() {
  const [form, setForm] = useState({
    partner_type: "CLINIC",
    organization_name: "",
    contact_email: "",
    contact_phone: "",
    domain: "",
  });
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/pilot-readiness/partner-registration`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(form),
      });
      const json = (await res.json().catch(() => ({}))) as { error?: unknown; data?: { registration_code?: string } };
      if (!res.ok) {
        const e = json.error;
        const message =
          typeof e === "string"
            ? e
            : e && typeof e === "object" && "message" in e
              ? String((e as { message: unknown }).message)
              : "";
        throw new Error(message || `Không gửi được đăng ký (lỗi ${res.status}). Vui lòng thử lại sau.`);
      }
      setResult(json.data?.registration_code ?? "Đã gửi");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Đăng ký không thành công");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6 p-6">
      <section>
        <Badge tone="info">Đăng ký đối tác</Badge>
        <h1 className="mt-3 text-2xl font-semibold text-slate-900">Đăng ký tổ chức của bạn</h1>
        <p className="mt-2 text-slate-600">
          Phòng khám, phòng xét nghiệm và bệnh viện có thể đăng ký trực tuyến. DxCon sẽ duyệt
          trước khi kích hoạt.
        </p>
      </section>

      <Card>
        <form className="space-y-4" onSubmit={submit}>
          <label className="block text-sm font-medium text-slate-700">
            Loại đối tác
            <select
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              value={form.partner_type}
              onChange={(e) => setForm({ ...form, partner_type: e.target.value })}
            >
              <option value="CLINIC">Phòng khám</option>
              <option value="LAB">Phòng xét nghiệm</option>
              <option value="HOSPITAL">Bệnh viện</option>
            </select>
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Tên tổ chức
            <input
              required
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              value={form.organization_name}
              onChange={(e) => setForm({ ...form, organization_name: e.target.value })}
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Email liên hệ
            <input
              required
              type="email"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              value={form.contact_email}
              onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Số điện thoại (không bắt buộc)
            <input
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              value={form.contact_phone}
              onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
            />
          </label>
          <Button type="submit" disabled={loading}>
            {loading ? "Đang gửi…" : "Gửi đăng ký"}
          </Button>
        </form>
      </Card>

      {result ? (
        <Card>
          <CardTitle>Đã nhận đăng ký</CardTitle>
          <CardDescription>Mã đăng ký: {result}. Trạng thái: chờ duyệt.</CardDescription>
        </Card>
      ) : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
    </div>
  );
}
