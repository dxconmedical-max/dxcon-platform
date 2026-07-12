"use client";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { BookingWizard } from "@/components/workspace/BookingWizard";

function BookPanel({ accessToken, organizationId, userName }: WorkspaceContext) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Book a service</h1>
        <p className="mt-1 text-sm text-slate-500">
          Select tests, choose a location or home collection, pick a time, and get a QR confirmation.
        </p>
      </div>
      <BookingWizard
        accessToken={accessToken}
        organizationId={organizationId}
        defaultContactName={userName}
      />
    </div>
  );
}

export default function PatientBookPage() {
  return (
    <WorkspaceScreen title="Book a service" workspacePath="/app/patient" permission="portal.patient.read">
      {(ctx) => <BookPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
