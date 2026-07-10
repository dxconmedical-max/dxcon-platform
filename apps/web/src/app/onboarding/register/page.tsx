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
      const json = await res.json();
      if (!res.ok) {
        throw new Error(json.error ?? `HTTP ${res.status}`);
      }
      setResult(json.data?.registration_code ?? "Submitted");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-xl space-y-6 p-6">
      <section>
        <Badge tone="info">Partner registration</Badge>
        <h1 className="mt-3 text-2xl font-semibold text-slate-900">Register your organization</h1>
        <p className="mt-2 text-slate-600">
          Clinics, laboratories, and hospitals can apply online. Admin approval is required before
          activation.
        </p>
      </section>

      <Card>
        <form className="space-y-4" onSubmit={submit}>
          <label className="block text-sm font-medium text-slate-700">
            Partner type
            <select
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              value={form.partner_type}
              onChange={(e) => setForm({ ...form, partner_type: e.target.value })}
            >
              <option value="CLINIC">Clinic</option>
              <option value="LAB">Laboratory</option>
              <option value="HOSPITAL">Hospital</option>
            </select>
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Organization name
            <input
              required
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              value={form.organization_name}
              onChange={(e) => setForm({ ...form, organization_name: e.target.value })}
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Contact email
            <input
              required
              type="email"
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              value={form.contact_email}
              onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
            />
          </label>
          <label className="block text-sm font-medium text-slate-700">
            Phone (optional)
            <input
              className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              value={form.contact_phone}
              onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
            />
          </label>
          <Button type="submit" disabled={loading}>
            {loading ? "Submitting…" : "Submit application"}
          </Button>
        </form>
      </Card>

      {result ? (
        <Card>
          <CardTitle>Application received</CardTitle>
          <CardDescription>Reference: {result}. Status: Pending review.</CardDescription>
        </Card>
      ) : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
    </div>
  );
}
