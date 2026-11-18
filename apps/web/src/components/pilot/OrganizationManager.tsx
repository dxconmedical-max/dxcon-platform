"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { normalizeApiError } from "@/lib/errors";
import { apiRequest } from "@/services/api";
import { useAuthStore } from "@/stores/authStore";

type Organization = {
  id: string;
  organization_code: string;
  organization_name: string;
  organization_type: string;
  status: string;
  address?: string | null;
  phone?: string | null;
  email?: string | null;
  contact_person?: string | null;
  tax_code?: string | null;
};

type FormState = {
  organization_code: string;
  organization_name: string;
  organization_type: string;
  status: string;
  address: string;
  phone: string;
  email: string;
  contact_person: string;
  tax_code: string;
};

const EMPTY: FormState = {
  organization_code: "",
  organization_name: "",
  organization_type: "CLINIC",
  status: "active",
  address: "",
  phone: "",
  email: "",
  contact_person: "",
  tax_code: "",
};

const TYPES: Array<[string, string]> = [
  ["CLINIC", "Phòng khám"],
  ["HOSPITAL", "Bệnh viện"],
  ["LABORATORY", "Phòng xét nghiệm"],
  ["CORPORATE", "Doanh nghiệp"],
  ["INSURANCE", "Bảo hiểm"],
  ["PARTNER", "Đối tác"],
];

const SELECT_CLASS =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900";

function fromOrg(org: Organization): FormState {
  return {
    organization_code: org.organization_code,
    organization_name: org.organization_name,
    organization_type: org.organization_type || "CLINIC",
    status: (org.status || "active").toLowerCase(),
    address: org.address ?? "",
    phone: org.phone ?? "",
    email: org.email ?? "",
    contact_person: org.contact_person ?? "",
    tax_code: org.tax_code ?? "",
  };
}

export function OrganizationManager() {
  const token = useAuthStore((s) => s.accessToken);
  const organizationId = useAuthStore((s) => s.activeOrganizationId);
  const [items, setItems] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiRequest<{ data: Organization[] }>(
        "/api/v1/partner/organizations?per_page=200",
        { token, organizationId },
      );
      setItems(res.data ?? []);
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

  function setField<K extends keyof FormState>(key: K, value: string) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function startEdit(org: Organization) {
    setEditingId(org.id);
    setForm(fromOrg(org));
    setNotice(null);
    setError(null);
  }

  function reset() {
    setEditingId(null);
    setForm(EMPTY);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    const code = form.organization_code.trim();
    const name = form.organization_name.trim();
    if (!code || !name) {
      setError("Cần nhập Mã và Tên tổ chức.");
      return;
    }
    if (!editingId && items.some((o) => o.organization_code === code)) {
      setError(`Mã ${code} đã tồn tại. Chọn mã khác hoặc bấm Sửa ở danh sách.`);
      return;
    }
    setSaving(true);
    try {
      const body = { ...form, organization_code: code, organization_name: name };
      if (editingId) {
        await apiRequest(`/api/v1/partner/organizations/${editingId}`, {
          method: "PUT",
          body,
          token,
          organizationId,
        });
        setNotice(`Đã cập nhật ${code}.`);
      } else {
        await apiRequest("/api/v1/partner/organizations", {
          method: "POST",
          body,
          token,
          organizationId,
        });
        setNotice(`Đã tạo ${code}.`);
      }
      reset();
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardTitle>{editingId ? "Sửa tổ chức" : "Thêm phòng khám / tổ chức"}</CardTitle>
        <CardDescription>
          Phòng khám phải ở trạng thái Hoạt động mới hiện trong danh sách chọn phòng khám của
          lễ tân.
        </CardDescription>
        <form onSubmit={submit} className="mt-4 grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="org-code">Mã tổ chức *</Label>
            <Input
              id="org-code"
              value={form.organization_code}
              disabled={Boolean(editingId)}
              onChange={(e) => setField("organization_code", e.target.value)}
              placeholder="VD: PK-ABC"
            />
          </div>
          <div>
            <Label htmlFor="org-name">Tên tổ chức *</Label>
            <Input
              id="org-name"
              value={form.organization_name}
              onChange={(e) => setField("organization_name", e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="org-type">Loại</Label>
            <select
              id="org-type"
              className={SELECT_CLASS}
              value={form.organization_type}
              onChange={(e) => setField("organization_type", e.target.value)}
            >
              {TYPES.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="org-status">Trạng thái</Label>
            <select
              id="org-status"
              className={SELECT_CLASS}
              value={form.status}
              onChange={(e) => setField("status", e.target.value)}
            >
              <option value="active">Hoạt động</option>
              <option value="inactive">Tạm ngưng</option>
            </select>
          </div>
          <div>
            <Label htmlFor="org-contact">Người liên hệ</Label>
            <Input
              id="org-contact"
              value={form.contact_person}
              onChange={(e) => setField("contact_person", e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="org-phone">Điện thoại</Label>
            <Input
              id="org-phone"
              value={form.phone}
              onChange={(e) => setField("phone", e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="org-email">Email</Label>
            <Input
              id="org-email"
              type="email"
              value={form.email}
              onChange={(e) => setField("email", e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="org-tax">Mã số thuế</Label>
            <Input
              id="org-tax"
              value={form.tax_code}
              onChange={(e) => setField("tax_code", e.target.value)}
            />
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="org-address">Địa chỉ</Label>
            <Input
              id="org-address"
              value={form.address}
              onChange={(e) => setField("address", e.target.value)}
            />
          </div>
          <div className="flex items-center gap-3 md:col-span-2">
            <Button type="submit" disabled={saving}>
              {saving ? "Đang lưu…" : editingId ? "Lưu thay đổi" : "Tạo tổ chức"}
            </Button>
            {editingId ? (
              <Button type="button" variant="outline" onClick={reset}>
                Hủy sửa
              </Button>
            ) : null}
            {notice ? <span className="text-sm text-teal-700">{notice}</span> : null}
            {error ? <span className="text-sm text-red-600">{error}</span> : null}
          </div>
        </form>
      </Card>

      <Card>
        <CardTitle>Danh sách tổ chức</CardTitle>
        {loading ? (
          <p className="mt-3 text-sm text-slate-500">Đang tải…</p>
        ) : items.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">Chưa có tổ chức nào.</p>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-slate-500">
                <tr>
                  <th className="py-2 pr-4">Mã</th>
                  <th className="py-2 pr-4">Tên</th>
                  <th className="py-2 pr-4">Loại</th>
                  <th className="py-2 pr-4">Trạng thái</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {items.map((org) => (
                  <tr key={org.id} className="border-t border-slate-100">
                    <td className="py-2 pr-4 font-mono">{org.organization_code}</td>
                    <td className="py-2 pr-4">{org.organization_name}</td>
                    <td className="py-2 pr-4">{org.organization_type}</td>
                    <td className="py-2 pr-4">
                      <Badge tone={org.status?.toLowerCase() === "active" ? "success" : "default"}>
                        {org.status}
                      </Badge>
                    </td>
                    <td className="py-2 text-right">
                      <Button size="sm" variant="outline" onClick={() => startEdit(org)}>
                        Sửa
                      </Button>
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
