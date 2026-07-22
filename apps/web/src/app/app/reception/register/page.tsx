"use client";

import Link from "next/link";
import { useState } from "react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { SectionHeader } from "@/components/workspace/primitives";
import { registerWalkIn, type WalkInRegistration } from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

const EMPTY: WalkInRegistration = {
  full_name: "",
  phone: "",
  date_of_birth: "",
  gender: "",
  national_id: "",
  note: "",
};

function RegisterPanel({ accessToken, organizationId }: WorkspaceContext) {
  const [form, setForm] = useState<WalkInRegistration>(EMPTY);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{ code: string; message: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const valid = form.full_name.trim().length > 1 && form.phone.trim().length > 5;

  function update(field: keyof WalkInRegistration, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const response = await registerWalkIn({ token: accessToken, organizationId }, form);
      setResult({
        code: response.value.patient_code,
        message: response.value.message,
      });
      setForm(EMPTY);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <SectionHeader title="Walk-in registration" description="Register a new walk-in patient." />

      {result ? (
        <Card className="flex flex-wrap items-center justify-between gap-3 border-emerald-200 bg-emerald-50/60">
          <div>
            <p className="font-medium text-emerald-900">{result.message}</p>
            <p className="text-sm text-emerald-800">Patient code: {result.code}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone="success">Registered</Badge>
            <Link href={`/app/reception/workflow?patient=${encodeURIComponent(result.code)}`}>
              <Button size="sm">Create order</Button>
            </Link>
          </div>
        </Card>
      ) : null}

      <Card className="space-y-4">
        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <Label htmlFor="full_name">Full name *</Label>
            <Input
              id="full_name"
              value={form.full_name}
              onChange={(e) => update("full_name", e.target.value)}
              placeholder="Patient full name"
            />
          </div>
          <div>
            <Label htmlFor="phone">Phone *</Label>
            <Input
              id="phone"
              value={form.phone}
              onChange={(e) => update("phone", e.target.value)}
              placeholder="Phone number"
            />
          </div>
          <div>
            <Label htmlFor="dob">Date of birth</Label>
            <Input
              id="dob"
              type="date"
              value={form.date_of_birth}
              onChange={(e) => update("date_of_birth", e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="gender">Gender</Label>
            <Input
              id="gender"
              value={form.gender}
              onChange={(e) => update("gender", e.target.value)}
              placeholder="Male / Female / Other"
            />
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="national_id">National ID</Label>
            <Input
              id="national_id"
              value={form.national_id ?? ""}
              onChange={(e) => update("national_id", e.target.value)}
              placeholder="National ID (optional)"
            />
          </div>
          <div className="md:col-span-2">
            <Label htmlFor="note">Note</Label>
            <Input
              id="note"
              value={form.note ?? ""}
              onChange={(e) => update("note", e.target.value)}
              placeholder="Optional note"
            />
          </div>
        </div>
        <div className="flex items-center gap-3 border-t border-slate-100 pt-4">
          <Button onClick={submit} disabled={!valid || submitting}>
            {submitting ? "Registering…" : "Register patient"}
          </Button>
          {error ? <span className="text-sm text-rose-600">{error}</span> : null}
        </div>
      </Card>
    </div>
  );
}

export default function ReceptionRegisterPage() {
  return (
    <WorkspaceScreen
      title="Walk-in registration"
      workspacePath="/app/reception"
      permission="reception.write"
    >
      {(ctx) => <RegisterPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
