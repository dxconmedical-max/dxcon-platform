"use client";

import { useState } from "react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { DataState, SectionHeader } from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import {
  fetchPatientProfile,
  updatePatientProfile,
  type PatientProfile,
} from "@/lib/api/patient-portal";
import type { DataSource } from "@/lib/api/adapter";
import { normalizeApiError } from "@/lib/errors";

function ProfileForm({
  initial,
  accessToken,
  organizationId,
}: {
  initial: PatientProfile;
  accessToken: string;
  organizationId: string;
}) {
  const [form, setForm] = useState<PatientProfile>(initial);
  const [saving, setSaving] = useState(false);
  const [savedSource, setSavedSource] = useState<DataSource | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  function update(field: keyof PatientProfile, value: string) {
    setForm((prev) => ({ ...prev, [field]: value }));
    setSavedSource(null);
  }

  async function save() {
    setSaving(true);
    setSaveError(null);
    try {
      const result = await updatePatientProfile(
        { token: accessToken, organizationId },
        {
          full_name: form.full_name,
          phone: form.phone,
          email: form.email,
          address: form.address,
        },
      );
      setForm(result.value);
      setSavedSource(result.source);
    } catch (error) {
      setSaveError(normalizeApiError(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <Label htmlFor="full_name">Full name</Label>
          <Input id="full_name" value={form.full_name} onChange={(e) => update("full_name", e.target.value)} />
        </div>
        <div>
          <Label htmlFor="patient_code">Patient code</Label>
          <Input id="patient_code" value={form.patient_code} disabled />
        </div>
        <div>
          <Label htmlFor="dob">Date of birth</Label>
          <Input id="dob" value={form.date_of_birth ?? ""} disabled />
        </div>
        <div>
          <Label htmlFor="gender">Gender</Label>
          <Input id="gender" value={form.gender ?? ""} disabled />
        </div>
        <div>
          <Label htmlFor="phone">Phone</Label>
          <Input id="phone" value={form.phone ?? ""} onChange={(e) => update("phone", e.target.value)} />
        </div>
        <div>
          <Label htmlFor="email">Email</Label>
          <Input id="email" value={form.email ?? ""} onChange={(e) => update("email", e.target.value)} />
        </div>
        <div className="md:col-span-2">
          <Label htmlFor="address">Address</Label>
          <Input id="address" value={form.address ?? ""} onChange={(e) => update("address", e.target.value)} />
        </div>
        <div>
          <Label htmlFor="blood_type">Blood type</Label>
          <Input id="blood_type" value={form.blood_type ?? ""} disabled />
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3 border-t border-slate-100 pt-4">
        <Button onClick={save} disabled={saving}>
          {saving ? "Saving…" : "Save changes"}
        </Button>
        {savedSource === "live" ? <span className="text-sm text-emerald-700">Profile updated.</span> : null}
        {savedSource === "sample" ? (
          <span className="text-sm text-amber-700">Saved locally (no live backend response).</span>
        ) : null}
        {saveError ? <span className="text-sm text-rose-600">{saveError}</span> : null}
      </div>
    </Card>
  );
}

function ProfilePanel({ accessToken, organizationId }: WorkspaceContext) {
  const state = useSourcedData<PatientProfile>(
    () => fetchPatientProfile({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );

  return (
    <div className="space-y-4">
      <SectionHeader
        title="My profile"
        description="Personal and contact details."
        source={state.source ?? undefined}
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={!state.data}
        emptyLabel="Profile unavailable."
        onRetry={state.reload}
      >
        {state.data ? (
          <ProfileForm
            key={state.data.patient_code}
            initial={state.data}
            accessToken={accessToken}
            organizationId={organizationId}
          />
        ) : null}
      </DataState>
    </div>
  );
}

export default function PatientProfilePage() {
  return (
    <WorkspaceScreen title="My profile" workspacePath="/app/patient" permission="portal.patient.read">
      {(ctx) => <ProfilePanel {...ctx} />}
    </WorkspaceScreen>
  );
}
