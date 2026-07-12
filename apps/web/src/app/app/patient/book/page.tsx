"use client";

import { useSearchParams } from "next/navigation";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { PatientCommerceBookingWizard } from "@/components/workspace/PatientCommerceBookingWizard";

function BookPanel({ accessToken, organizationId, userName }: WorkspaceContext) {
  const params = useSearchParams();
  const listing = params.get("listing") ?? undefined;
  const provider = params.get("provider") ?? undefined;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Book a service</h1>
        <p className="mt-1 text-sm text-slate-500">
          Choose patient, service, provider, schedule, collection type, review pricing, and pay securely.
        </p>
      </div>
      <PatientCommerceBookingWizard
        accessToken={accessToken}
        organizationId={organizationId}
        defaultContactName={userName}
        initialListingId={listing}
        initialProviderId={provider}
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
