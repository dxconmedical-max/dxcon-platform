"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { normalizeApiError } from "@/lib/errors";
import { apiRequest } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";

type StaffUser = {
  id: string;
  email: string;
  role: string;
  organization_id?: string | null;
  is_active: boolean;
};

type Org = { id: string; organization_code: string; organization_name: string; status: string };

// platform role -> organization membership role
const ROLES: Array<[string, string, string]> = [
  ["RECEPTION", "Tiếp nhận", "RECEPTION"],
  ["LAB", "Phòng xét nghiệm", "LAB"],
  ["COLLECTOR", "Thu mẫu", "COLLECTOR"],
  ["DOCTOR", "Bác sĩ", "DOCTOR"],
  ["ACCOUNTING", "Kế toán", "FINANCE"],
  ["ADMIN", "Quản trị", "ORG_OWNER"],
];

const SELECT_CLASS =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";

const ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";

function generatePassword(length = 16): string {
  const bytes = new Uint32Array(length);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (n) => ALPHABET[n % ALPHABET.length]).join("");
}

export function StaffManager() {
  const token = useAuthStore((s) => s.accessToken);
  const organizationId = useAuthStore((s) => s.activeOrganizationId);
  const myEmail = useAuthStore((s) => s.user?.email ?? null);
  const [users, setUsers] = useState<StaffUser[]>([]);
  const [orgs, setOrgs] = useState<Org[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [created, setCreated] = useState<{ email: string; password: string } | null>(null);
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [role, setRole] = useState("RECEPTION");
  const [orgId, setOrgId] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [u, o] = await Promise.all([
        apiRequest<{ users: StaffUser[] }>("/api/v1/security/users", { token, organizationId }),
        apiRequest<{ data: Org[] }>("/api/v1/partner/organizations?per_page=200", {
          token,
          organizationId,
        }),
      ]);
      setUsers(u.users ?? []);
      const list = (o.data ?? []).filter((x) => (x.status || "").toLowerCase() === "active");
      setOrgs(list);
      setOrgId((prev) => prev || list.find((x) => x.organization_code === "DXCON_INTERNAL")?.id || list[0]?.id || "");
      setError(null);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [token, organizationId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function createStaff(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setCreated(null);
    const cleanEmail = email.trim().toLowerCase();
    if (!cleanEmail || !cleanEmail.includes("@")) {
      setError("Cần nhập email hợp lệ.");
      return;
    }
    if (!orgId) {
      setError("Chọn tổ chức cho tài khoản.");
      return;
    }
    const orgRole = ROLES.find((r) => r[0] === role)?.[2] ?? "VIEWER";
    const password = generatePassword();
    setSaving(true);
    let userId: string | null = null;
    try {
      const res = await apiRequest<{ user: StaffUser }>("/api/v1/security/users", {
        method: "POST",
        body: { email: cleanEmail, phone: phone.trim() || undefined, password, role },
        token,
        organizationId,
      });
      userId = res.user.id;
      await apiRequest("/api/v1/partner/users/invite", {
        method: "POST",
        body: { organization_id: orgId, user_id: userId, role_code: orgRole },
        token,
        organizationId,
      });
      setCreated({ email: cleanEmail, password });
      setEmail("");
      setPhone("");
      await load();
    } catch (err) {
      const msg = normalizeApiError(err);
      setError(
        userId
          ? `Đã tạo tài khoản ${cleanEmail} nhưng gắn vào tổ chức thất bại: ${msg}. Liên hệ để xử lý, đừng tạo lại.`
          : msg,
      );
      if (userId) await load();
    } finally {
      setSaving(false);
    }
  }

  async function disable(user: StaffUser) {
    setError(null);
    setNotice(null);
    try {
      await apiRequest(`/api/v1/security/users/${encodeURIComponent(user.id)}/disable`, {
        method: "POST",
        token,
        organizationId,
      });
      setConfirmId(null);
      setNotice(`Đã khóa ${user.email}.`);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    }
  }

  const orgName = (id?: string | null) =>
    orgs.find((o) => o.id === id)?.organization_name ?? (id ? id.slice(0, 8) : "—");

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle>Tạo tài khoản nhân viên</CardTitle>
        <CardDescription>
          Hệ thống tạo mật khẩu ngẫu nhiên và chỉ hiển thị một lần ngay sau khi tạo. Gửi riêng cho
          nhân viên, không dán vào chat hay email chung.
        </CardDescription>
        <form onSubmit={createStaff} className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="st-email">Email *</Label>
            <Input
              id="st-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="st-phone">Điện thoại</Label>
            <Input id="st-phone" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="st-role">Vai trò</Label>
            <select
              id="st-role"
              className={SELECT_CLASS}
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              {ROLES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="st-org">Tổ chức</Label>
            <select
              id="st-org"
              className={SELECT_CLASS}
              value={orgId}
              onChange={(e) => setOrgId(e.target.value)}
            >
              {orgs.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.organization_name} ({o.organization_code})
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-3 md:col-span-2">
            <Button type="submit" disabled={saving}>
              {saving ? "Đang tạo…" : "Tạo tài khoản"}
            </Button>
            {notice ? <span className="text-sm text-teal-700">{notice}</span> : null}
            {error ? <span className="text-sm text-red-600">{error}</span> : null}
          </div>
        </form>
        {created ? (
          <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm">
            <p className="font-medium text-slate-900">
              Đã tạo {created.email}. Mật khẩu tạm (chỉ hiện lần này):
            </p>
            <p className="mt-2 select-all font-mono text-lg text-slate-900">{created.password}</p>
            <p className="mt-2 text-slate-600">
              Chép ngay và gửi riêng cho nhân viên. Tải lại trang là mất.
            </p>
          </div>
        ) : null}
      </Card>

      <Card>
        <CardTitle>Tài khoản hiện có</CardTitle>
        {loading ? (
          <p className="mt-3 text-sm text-slate-500">Đang tải…</p>
        ) : users.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">Chưa có tài khoản.</p>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-slate-500">
                <tr>
                  <th className="py-2 pr-4">Email</th>
                  <th className="py-2 pr-4">Vai trò</th>
                  <th className="py-2 pr-4">Tổ chức</th>
                  <th className="py-2 pr-4">Trạng thái</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id} className="border-t border-slate-100">
                    <td className="py-2 pr-4">{u.email}</td>
                    <td className="py-2 pr-4">{u.role}</td>
                    <td className="py-2 pr-4">{orgName(u.organization_id)}</td>
                    <td className="py-2 pr-4">
                      <Badge tone={u.is_active ? "success" : "default"}>
                        {u.is_active ? "Hoạt động" : "Đã khóa"}
                      </Badge>
                    </td>
                    <td className="py-2 text-right">
                      {u.is_active && u.email !== myEmail ? (
                        confirmId === u.id ? (
                          <span className="inline-flex gap-2">
                            <Button size="sm" variant="secondary" onClick={() => void disable(u)}>
                              Xác nhận khóa
                            </Button>
                            <Button size="sm" variant="ghost" onClick={() => setConfirmId(null)}>
                              Hủy
                            </Button>
                          </span>
                        ) : (
                          <Button size="sm" variant="outline" onClick={() => setConfirmId(u.id)}>
                            Khóa
                          </Button>
                        )
                      ) : null}
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
