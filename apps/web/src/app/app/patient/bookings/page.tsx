"use client";

import Link from "next/link";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Button } from "@/components/ui/Button";
import {
  DataState,
  SectionHeader,
  SimpleTable,
  StatusPill,
} from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchPatientBookings, type PatientBooking } from "@/lib/api/patient-portal";

function BookingsPanel({ accessToken, organizationId }: WorkspaceContext) {
  const state = useSourcedData<PatientBooking[]>(
    () => fetchPatientBookings({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const rows = state.data ?? [];

  return (
    <div className="space-y-4">
      <SectionHeader
        title="My bookings"
        description="Scheduled collections and visits."
        source={state.source ?? undefined}
        actions={
          <Link href="/app/patient/book">
            <Button size="sm">New booking</Button>
          </Link>
        }
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={rows.length === 0}
        emptyLabel="No bookings yet. Create your first booking to get started."
        onRetry={state.reload}
      >
        <SimpleTable<PatientBooking>
          rows={rows}
          rowKey={(row) => row.reference}
          columns={[
            { key: "reference", label: "Reference", render: (r) => r.reference },
            { key: "service", label: "Service", render: (r) => r.service },
            { key: "scheduled", label: "Scheduled", render: (r) => r.scheduled_at },
            { key: "location", label: "Location", render: (r) => r.location },
            { key: "status", label: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
        />
      </DataState>
    </div>
  );
}

export default function PatientBookingsPage() {
  return (
    <WorkspaceScreen title="My bookings" workspacePath="/app/patient" permission="portal.patient.read">
      {(ctx) => <BookingsPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
