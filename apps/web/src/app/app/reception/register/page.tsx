"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import {
  getDuplicateWarnings,
  registerWalkIn,
  type DuplicateWarning,
} from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

import { SectionHeader } from "../_components/ui";

function RegisterPanel() {
  const router = useRouter();
  const { accessToken, activeOrganizationId } = useAuth();
  const [form, setForm] = useState({
    full_name: "",
    phone: "",
    national_id: "",
    gender: "",
    date_of_birth: "",
    email: "",
    address: "",
  });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duplicates, setDuplicates] = useState<DuplicateWarning[]>([]);

  async function submit(force = false) {
    if (!accessToken) return;
    if (!form.full_name.trim() || !form.phone.trim()) {
      setError("Full name and phone are required.");
      return;
    }
    setCreating(true);
    setError(null);
    if (!force) setDuplicates([]);
    try {
      const result = await registerWalkIn(
        { token: accessToken, organizationId: activeOrganizationId },
        {
          full_name: form.full_name.trim(),
          phone: form.phone.trim(),
          national_id: form.national_id.trim() || undefined,
          gender: form.gender.trim() || undefined,
          date_of_birth: form.date_of_birth.trim() || undefined,
          email: form.email.trim() || undefined,
          address: form.address.trim() || undefined,
          force,
        },
      );
      router.push(`/app/reception/workflow?patient=${encodeURIComponent(result.patient_code)}`);
    } catch (err) {
      const warnings = getDuplicateWarnings(err);
      if (warnings.length > 0) {
        setDuplicates(warnings);
        setError("Possible duplicate patient. Use an existing match or register anyway.");
      } else {
        setError(normalizeApiError(err));
      }
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Register walk-in patient"
        description="Creates a patient via the production reception workspace API with duplicate detection."
        actions={
          <Link href="/app/reception/search">
            <Button size="sm" variant="outline">
              Search instead
            </Button>
          </Link>
        }
      />
      <Card className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="full_name">Full name *</Label>
            <Input
              id="full_name"
              value={form.full_name}
              onChange={(event) => setForm((prev) => ({ ...prev, full_name: event.target.value }))}
            />
          </div>
          <div>
            <Label htmlFor="phone">Phone *</Label>
            <Input
              id="phone"
              value={form.phone}
              onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
            />
          </div>
          <div>
            <Label htmlFor="national_id">National ID</Label>
            <Input
              id="national_id"
              value={form.national_id}
              onChange={(event) => setForm((prev) => ({ ...prev, national_id: event.target.value }))}
            />
          </div>
          <div>
            <Label htmlFor="gender">Gender</Label>
            <Input
              id="gender"
              value={form.gender}
              onChange={(event) => setForm((prev) => ({ ...prev, gender: event.target.value }))}
            />
          </div>
          <div>
            <Label htmlFor="dob">Date of birth</Label>
            <Input
              id="dob"
              type="date"
              value={form.date_of_birth}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, date_of_birth: event.target.value }))
              }
            />
          </div>
          <div>
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              value={form.email}
              onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
            />
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="address">Address</Label>
            <Input
              id="address"
              value={form.address}
              onChange={(event) => setForm((prev) => ({ ...prev, address: event.target.value }))}
            />
          </div>
        </div>
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        {duplicates.length > 0 ? (
          <div className="space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-3">
            <p className="text-sm font-medium text-amber-900">Duplicate detection</p>
            <ul className="space-y-2 text-sm text-amber-900">
              {duplicates.map((warning, index) => (
                <li
                  key={`${warning.patient_code ?? warning.field ?? "dup"}-${index}`}
                  className="flex flex-wrap items-center justify-between gap-2"
                >
                  <span>
                    {String(warning.message ?? warning.reason ?? "Possible match")}
                    {warning.patient_code ? ` (${warning.patient_code})` : ""}
                  </span>
                  {warning.patient_code ? (
                    <Link
                      href={`/app/reception/workflow?patient=${encodeURIComponent(String(warning.patient_code))}`}
                    >
                      <Button size="sm" variant="outline">
                        Use existing
                      </Button>
                    </Link>
                  ) : null}
                </li>
              ))}
            </ul>
            <Button variant="secondary" disabled={creating} onClick={() => void submit(true)}>
              {creating ? "Registering…" : "Register anyway"}
            </Button>
          </div>
        ) : null}
        <Button disabled={creating || !accessToken} onClick={() => void submit(false)}>
          {creating ? "Registering…" : "Register patient"}
        </Button>
      </Card>
    </div>
  );
}

export default function ReceptionRegisterPage() {
  return (
    <AppShell title="Register patient" workspacePath="/app/reception">
      <RegisterPanel />
    </AppShell>
  );
}
