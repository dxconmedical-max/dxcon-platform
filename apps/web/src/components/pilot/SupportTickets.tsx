"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { normalizeApiError } from "@/lib/errors";
import { apiRequest } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";

type Ticket = {
  ticket_code: string;
  subject: string;
  description?: string | null;
  category?: string | null;
  priority?: string | null;
  status: string;
  requester_email?: string | null;
  created_at?: string | null;
};

const STATUSES: Array<[string, string]> = [
  ["OPEN", "Mới"],
  ["IN_PROGRESS", "Đang xử lý"],
  ["WAITING", "Chờ phản hồi"],
  ["RESOLVED", "Đã giải quyết"],
  ["CLOSED", "Đã đóng"],
];

const PRIORITIES: Array<[string, string]> = [
  ["LOW", "Thấp"],
  ["NORMAL", "Bình thường"],
  ["HIGH", "Cao"],
  ["URGENT", "Khẩn"],
];

const SELECT_CLASS =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";

export function SupportTickets() {
  const token = useAuthStore((s) => s.accessToken);
  const organizationId = useAuthStore((s) => s.activeOrganizationId);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("NORMAL");
  const [requesterEmail, setRequesterEmail] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const query = filter ? `?status=${encodeURIComponent(filter)}` : "";
      const res = await apiRequest<{ data: { data: Ticket[] } }>(
        `/api/v1/operations-center/support-tickets${query}`,
        { token, organizationId },
      );
      setTickets(res.data?.data ?? []);
      setError(null);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [token, organizationId, filter]);

  useEffect(() => {
    void load();
  }, [load]);

  async function createTicket(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    if (!subject.trim()) {
      setError("Cần nhập tiêu đề yêu cầu.");
      return;
    }
    setSaving(true);
    try {
      const res = await apiRequest<{ data: Ticket }>(
        "/api/v1/operations-center/support-tickets",
        {
          method: "POST",
          body: {
            subject: subject.trim(),
            description: description.trim() || undefined,
            priority,
            requester_email: requesterEmail.trim() || undefined,
          },
          token,
          organizationId,
        },
      );
      setNotice(`Đã tạo ${res.data.ticket_code}.`);
      setSubject("");
      setDescription("");
      setRequesterEmail("");
      setPriority("NORMAL");
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(code: string, status: string) {
    setError(null);
    setNotice(null);
    try {
      await apiRequest(
        `/api/v1/operations-center/support-tickets/${encodeURIComponent(code)}/status`,
        { method: "POST", body: { status }, token, organizationId },
      );
      setNotice(`Đã cập nhật ${code}.`);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle>Tạo yêu cầu hỗ trợ</CardTitle>
        <CardDescription>
          Ghi lại sự cố hoặc yêu cầu của khách hàng để theo dõi đến khi giải quyết.
        </CardDescription>
        <form onSubmit={createTicket} className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <Label htmlFor="tk-subject">Tiêu đề *</Label>
            <Input
              id="tk-subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="tk-desc">Mô tả</Label>
            <textarea
              id="tk-desc"
              rows={3}
              className={SELECT_CLASS}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="tk-priority">Mức ưu tiên</Label>
            <select
              id="tk-priority"
              className={SELECT_CLASS}
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
            >
              {PRIORITIES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="tk-email">Email người yêu cầu</Label>
            <Input
              id="tk-email"
              type="email"
              value={requesterEmail}
              onChange={(e) => setRequesterEmail(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-3 md:col-span-2">
            <Button type="submit" disabled={saving}>
              {saving ? "Đang lưu…" : "Tạo yêu cầu"}
            </Button>
            {notice ? <span className="text-sm text-teal-700">{notice}</span> : null}
            {error ? <span className="text-sm text-red-600">{error}</span> : null}
          </div>
        </form>
      </Card>

      <Card>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <CardTitle>Danh sách yêu cầu</CardTitle>
          <select
            aria-label="Lọc theo trạng thái"
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          >
            <option value="">Tất cả</option>
            {STATUSES.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        {loading ? (
          <p className="mt-3 text-sm text-slate-500">Đang tải…</p>
        ) : tickets.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">Chưa có yêu cầu nào.</p>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-slate-500">
                <tr>
                  <th className="py-2 pr-4">Mã</th>
                  <th className="py-2 pr-4">Tiêu đề</th>
                  <th className="py-2 pr-4">Ưu tiên</th>
                  <th className="py-2 pr-4">Người yêu cầu</th>
                  <th className="py-2 pr-4">Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((t) => (
                  <tr key={t.ticket_code} className="border-t border-slate-100 align-top">
                    <td className="py-2 pr-4 font-mono">{t.ticket_code}</td>
                    <td className="py-2 pr-4">
                      <div className="font-medium text-slate-900">{t.subject}</div>
                      {t.description ? (
                        <div className="text-xs text-slate-500">{t.description}</div>
                      ) : null}
                    </td>
                    <td className="py-2 pr-4">
                      <Badge tone={t.priority === "URGENT" || t.priority === "HIGH" ? "info" : "default"}>
                        {t.priority ?? "NORMAL"}
                      </Badge>
                    </td>
                    <td className="py-2 pr-4">{t.requester_email ?? "—"}</td>
                    <td className="py-2 pr-4">
                      <select
                        aria-label={`Trạng thái ${t.ticket_code}`}
                        className="rounded-lg border border-slate-300 bg-white px-2 py-1 text-sm"
                        value={t.status}
                        onChange={(e) => void changeStatus(t.ticket_code, e.target.value)}
                      >
                        {STATUSES.map(([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
