"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/workspace/primitives";
import type { ReceptionOrderCreate } from "@/lib/api/reception";

import {
  formatCurrency,
  PatientStep,
  TestsStep,
  type SelectedPatient,
} from "./OrderSteps";

const STEPS = ["Patient", "Tests & order", "Order created"] as const;

function ReceptionOrderWorkflowPanel({ accessToken, organizationId }: WorkspaceContext) {
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

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Create diagnostic order"
        description="Search or register a patient, select tests, and create an order. Payment and lab dispatch are Milestone 2+."
        actions={
          step > 0 ? (
            <Button size="sm" variant="outline" onClick={reset}>
              Start over
            </Button>
          ) : undefined
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
          organizationId={organizationId}
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
          organizationId={organizationId}
          patient={patient}
          onOrderCreated={(ref, orderPricing) => {
            setOrderRef(ref);
            setPricing(orderPricing);
            setStep(2);
          }}
        />
      ) : null}

      {step === 2 && patient && orderRef && pricing ? (
        <Card className="space-y-4">
          <SectionHeader
            title="Order created"
            description="Milestone 1 complete. Payment, barcodes, and lab queue are next milestones."
          />
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs text-slate-500">Patient</p>
              <p className="font-medium text-slate-900">{patient.patientName}</p>
              <p className="text-xs text-slate-500">{patient.patientCode}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs text-slate-500">Order total</p>
              <p className="font-semibold text-slate-900">{formatCurrency(pricing.total)}</p>
              <p className="text-xs text-slate-500">
                Subtotal {formatCurrency(pricing.subtotal)} · Discount{" "}
                {formatCurrency(pricing.discount)}
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
              <p className="text-xs text-slate-500">Order code</p>
              <p className="break-all font-mono text-sm">{orderRef}</p>
              <p className="text-xs text-slate-500">Status: payment pending</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-3 border-t border-slate-100 pt-4">
            <Button onClick={reset}>New order</Button>
            <Link href="/app/reception">
              <Button variant="outline">Back to dashboard</Button>
            </Link>
            <Link href="/app/reception/search">
              <Button variant="ghost">Patient search</Button>
            </Link>
          </div>
        </Card>
      ) : null}
    </div>
  );
}

export default function ReceptionWorkflowPage() {
  return (
    <WorkspaceScreen title="Create order" workspacePath="/app/reception" permission="reception.write">
      {(ctx) => (
        <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
          <ReceptionOrderWorkflowPanel {...ctx} />
        </Suspense>
      )}
    </WorkspaceScreen>
  );
}
