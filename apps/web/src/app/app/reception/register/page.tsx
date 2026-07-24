"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useRef, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import {
  fetchReceptionPatient,
  getDuplicateWarnings,
  registerWalkIn,
  searchReceptionPatients,
  type DuplicateWarning,
} from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

import { SectionHeader } from "../_components/ui";

function RegisterPanel() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const returnQuery = searchParams.get("q") ?? "";
  const { accessToken, activeOrganizationId, can, role } = useAuth();
  const [form, setForm] = useState({
    full_name: "",
    phone: "",
    national_id: "",
    gender: "",
    date_of_birth: "",
    email: "",
    address: "",
    patient_code: "",
  });
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [duplicates, setDuplicates] = useState<DuplicateWarning[]>([]);
  const inFlight = useRef(false);

  const canWrite =
    can("reception.write") ||
    can("patients.create") ||
    ["RECEPTION", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN", "PARTNER_RECEPTION"].includes(
      role ?? "",
    );

  async function submit(force = false) {
    if (!accessToken || inFlight.current) return;
    if (!form.full_name.trim() || !form.phone.trim()) {
      setError("Full name and phone are required.");
      return;
    }
    inFlight.current = true;
    setCreating(true);
    setError(null);
    if (!force) setDuplicates([]);
    try {
      if (!force) {
        const probe = await searchReceptionPatients(
          { token: accessToken, organizationId: activeOrganizationId },
          form.phone.trim() || form.national_id.trim(),
        );
        const matches = probe.items.filter(
          (p) =>
            (form.phone.trim() && p.phone === form.phone.trim()) ||
            (form.national_id.trim() && p.national_id === form.national_id.trim()),
        );
        if (matches.length > 0) {
          setDuplicates(
            matches.map((p) => ({
              patient_code: p.patient_code,
              full_name: p.full_name,
              message: `Existing patient ${p.full_name}`,
            })),
          );
          setError("Possible duplicate patient. Use an existing match or register anyway.");
          return;
        }
      }

      const result = await registerWalkIn(
        { token: accessToken, organizationId: activeOrganizationId, timeoutMs: 30_000 },
        {
          full_name: form.full_name.trim(),
          phone: form.phone.trim(),
          national_id: form.national_id.trim() || undefined,
          gender: form.gender.trim() || undefined,
          date_of_birth: form.date_of_birth.trim() || undefined,
          email: form.email.trim() || undefined,
          address: form.address.trim() || undefined,
          patient_code: form.patient_code.trim() || undefined,
          force,
        },
      );
      await fetchReceptionPatient(
        { token: accessToken, organizationId: activeOrganizationId },
        result.patient_code,
      );
      router.push(
        `/app/reception/workflow?patient=${encodeURIComponent(result.patient_code)}`,
      );
    } catch (err) {
      const warnings = getDuplicateWarnings(err);
      if (warnings.length > 0) {
        setDuplicates(warnings);
        setError("Possible duplicate patient. Use an existing match or register anyway.");
      } else {
        setError(normalizeApiError(err));
      }
    } finally {
      inFlight.current = false;
      setCreating(false);
    }
  }

  if (!canWrite) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        Reception write permission is required to register patients.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Register walk-in patient"
        description="Creates a patient via the production reception workspace API with duplicate detection."
        actions={
          <Link
            href={`/app/reception/search${returnQuery ? `?q=${encodeURIComponent(returnQuery)}` : ""}`}
          >
            <Button size="sm" variant="outline">
              Back to search
            </Button>
          </Link>
        }
      />
      <Card className="space-y-4">
        <p className="text-sm text-slate-600">
          Required fields are marked with *. Duplicate phone or national ID is detected before create.
        </p>
        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault();
            void submit(false);
          }}
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="full_name">Full name *</Label>
              <Input
                id="full_name"
                required
                autoComplete="name"
                value={form.full_name}
                onChange={(event) => setForm((prev) => ({ ...prev, full_name: event.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="phone">Phone *</Label>
              <Input
                id="phone"
                required
                autoComplete="tel"
                inputMode="tel"
                value={form.phone}
                onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="patient_code">Patient code (optional)</Label>
              <Input
                id="patient_code"
                value={form.patient_code}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, patient_code: event.target.value }))
                }
              />
            </div>
            <div>
              <Label htmlFor="national_id">National ID</Label>
              <Input
                id="national_id"
                value={form.national_id}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, national_id: event.target.value }))
                }
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
                autoComplete="email"
                value={form.email}
                onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="address">Address</Label>
              <Input
                id="address"
                autoComplete="street-address"
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
                        <Button size="sm" variant="outline" type="button">
                          Use existing
                        </Button>
                      </Link>
                    ) : null}
                  </li>
                ))}
              </ul>
              <Button
                type="button"
                variant="secondary"
                disabled={creating}
                onClick={() => void submit(true)}
              >
                {creating ? "Registering…" : "Register anyway"}
              </Button>
            </div>
          ) : null}
          <Button type="submit" disabled={creating || !accessToken}>
            {creating ? "Registering…" : "Register patient"}
          </Button>
        </form>
      </Card>
    </div>
  );
}

export default function ReceptionRegisterPage() {
  return (
    <AppShell title="Register patient" workspacePath="/app/reception">
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <RegisterPanel />
      </Suspense>
    </AppShell>
  );
}
