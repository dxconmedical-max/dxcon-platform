"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import {
  fetchReceptionOrder,
  type ReceptionOrderCreate,
  type ReceptionOrderPricing,
} from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

import { SectionHeader } from "../_components/ui";
import {
  OrderCreatedStep,
  PatientStep,
  TestsStep,
  type SelectedPatient,
} from "./OrderSteps";

const STEPS = ["Patient", "Tests & order", "Order created"] as const;

function ReceptionOrderWorkflowPanel() {
  const { accessToken, activeOrganizationId, can, role } = useAuth();
  const searchParams = useSearchParams();
  const patientParam = searchParams.get("patient") ?? undefined;
  const orderParam = searchParams.get("order") ?? undefined;
  const orderPatientParam = searchParams.get("orderPatient") ?? patientParam;

  const [step, setStep] = useState(0);
  const [patient, setPatient] = useState<SelectedPatient | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [orderRef, setOrderRef] = useState<string | null>(null);
  const [pricing, setPricing] = useState<ReceptionOrderPricing | null>(null);
  const [order, setOrder] = useState<ReceptionOrderCreate["order"] | null>(null);
  const [reopenError, setReopenError] = useState<string | null>(null);
  const [reopening, setReopening] = useState(Boolean(orderParam));

  const onQueryChange = useCallback((q: string) => setSearchQuery(q), []);

  const canWrite =
    can("reception.write") ||
    can("orders.create") ||
    can("patients.create") ||
    ["RECEPTION", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN", "PARTNER_RECEPTION"].includes(
      role ?? "",
    );

  useEffect(() => {
    if (!orderParam || !accessToken) {
      setReopening(false);
      return;
    }
    let cancelled = false;
    setReopening(true);
    setReopenError(null);
    void fetchReceptionOrder(
      { token: accessToken, organizationId: activeOrganizationId },
      orderParam,
      { patientCode: orderPatientParam },
    )
      .then((result) => {
        if (cancelled) return;
        const row = result.order as Record<string, unknown>;
        setPatient({
          patientCode: String(row.patient_code ?? row.patient_id ?? orderPatientParam ?? ""),
          patientName: String(row.patient_name ?? row.patient_code ?? "Patient"),
        });
        setOrderRef(String(row.order_code ?? orderParam));
        setPricing(result.pricing);
        setOrder(result.order);
        setStep(2);
      })
      .catch((err) => {
        if (!cancelled) setReopenError(normalizeApiError(err));
      })
      .finally(() => {
        if (!cancelled) setReopening(false);
      });
    return () => {
      cancelled = true;
    };
  }, [orderParam, orderPatientParam, accessToken, activeOrganizationId]);

  function reset() {
    setStep(0);
    setPatient(null);
    setOrderRef(null);
    setPricing(null);
    setOrder(null);
    setReopenError(null);
  }

  if (!accessToken) {
    return <p className="text-sm text-slate-500">Waiting for session…</p>;
  }

  if (!canWrite) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        Reception write permission is required to create patients and orders.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Reception Milestone 1 — Patient & order"
        description="Search or create a patient, select catalog tests, and create an order. Payment and barcode are not included in this milestone."
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

      {reopening ? <p className="text-sm text-slate-500">Reopening order…</p> : null}
      {reopenError ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {reopenError}
        </div>
      ) : null}

      {!reopening && step === 0 ? (
        <PatientStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          initialQuery={patientParam}
          preservedQuery={searchQuery || undefined}
          onQueryChange={onQueryChange}
          onSelect={(selected) => {
            setPatient(selected);
            setStep(1);
          }}
        />
      ) : null}

      {!reopening && step === 1 && patient ? (
        <TestsStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          onOrderCreated={(ref, orderPricing, createdOrder) => {
            setOrderRef(ref);
            setPricing(orderPricing);
            setOrder(createdOrder);
            setStep(2);
          }}
        />
      ) : null}

      {!reopening && step === 2 && patient && orderRef && pricing && order ? (
        <OrderCreatedStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          orderRef={orderRef}
          pricing={pricing}
          order={order}
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
