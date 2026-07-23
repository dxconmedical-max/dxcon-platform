"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import type { ReceptionOrderCreate } from "@/lib/api/reception";

import { SectionHeader } from "../_components/ui";
import {
  FulfillmentStep,
  PatientStep,
  TestsStep,
  type SelectedPatient,
} from "./OrderSteps";

const STEPS = ["Patient", "Tests & order", "Payment & documents"] as const;

function ReceptionOrderWorkflowPanel() {
  const { accessToken, activeOrganizationId } = useAuth();
  const searchParams = useSearchParams();
  const patientParam = searchParams.get("patient") ?? undefined;

  const [step, setStep] = useState(0);
  const [patient, setPatient] = useState<SelectedPatient | null>(null);
  const [orderRef, setOrderRef] = useState<string | null>(null);
  const [pricing, setPricing] = useState<ReceptionOrderCreate["pricing"] | null>(null);

  function reset() {
    setStep(0);
    setPatient(null);
    setOrderRef(null);
    setPricing(null);
  }

  if (!accessToken) {
    return <p className="text-sm text-slate-500">Waiting for session…</p>;
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Reception production workflow"
        description="Patient search/create, catalog selection, order pricing, payment, barcode, requisition, and QR — all via production APIs."
        actions={
          step > 0 ? (
            <Button size="sm" variant="outline" onClick={reset}>
              Start over
            </Button>
          ) : (
            <Link href="/app/reception">
              <Button size="sm" variant="ghost">
                Dashboard
              </Button>
            </Link>
          )
        }
      />

      <div className="flex flex-wrap gap-2">
        {STEPS.map((label, index) => (
          <Badge key={label} tone={index === step ? "info" : index < step ? "success" : "default"}>
            {index + 1}. {label}
          </Badge>
        ))}
      </div>

      {step === 0 ? (
        <PatientStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          initialQuery={patientParam}
          onSelect={(selected) => {
            setPatient(selected);
            setStep(1);
          }}
        />
      ) : null}

      {step === 1 && patient ? (
        <TestsStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          onOrderCreated={(ref, orderPricing) => {
            setOrderRef(ref);
            setPricing(orderPricing);
            setStep(2);
          }}
        />
      ) : null}

      {step === 2 && patient && orderRef && pricing ? (
        <FulfillmentStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          orderRef={orderRef}
          pricing={pricing}
          onReset={reset}
        />
      ) : null}
    </div>
  );
}

export default function ReceptionWorkflowPage() {
  return (
    <AppShell title="Create order" workspacePath="/app/reception">
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <ReceptionOrderWorkflowPanel />
      </Suspense>
    </AppShell>
  );
}
