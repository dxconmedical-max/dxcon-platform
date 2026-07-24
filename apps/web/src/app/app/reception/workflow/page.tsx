"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import {
  fetchReceptionOrder,
  type ReceptionOrderCreate,
  type ReceptionOrderPricing,
} from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

import { JourneyStepper, SectionHeader } from "../_components/ui";
import {
  PaymentStep,
  PatientStep,
  TestsStep,
  type SelectedPatient,
} from "./OrderSteps";

const STEPS = ["Patient", "Tests & order number", "Payment & documents"] as const;

function ReceptionOrderWorkflowPanel() {
  const { accessToken, activeOrganizationId, can, role, user } = useAuth();
  const searchParams = useSearchParams();
  const patientParam = searchParams.get("patient") ?? undefined;
  const orderParam = searchParams.get("order") ?? undefined;

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

  const cashierLabel =
    user && typeof user === "object"
      ? String(
          (user as { email?: string; full_name?: string; name?: string }).email ??
            (user as { full_name?: string }).full_name ??
            (user as { name?: string }).name ??
            "",
        ) || null
      : null;

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
    )
      .then((result) => {
        if (cancelled) return;
        const row = result.order as Record<string, unknown>;
        setPatient({
          patientCode: String(row.patient_code ?? row.patient_id ?? ""),
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
  }, [orderParam, accessToken, activeOrganizationId]);

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
        Reception write permission is required for orders, payment, and documents.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Reception Phase 1 — Order workflow"
        description="Patient → test catalog → laboratory order number → payment → barcode labels → printable order form."
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

      <JourneyStepper steps={STEPS} activeIndex={step} />

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
        <PaymentStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          orderRef={orderRef}
          pricing={pricing}
          order={order}
          onReset={reset}
          cashierLabel={cashierLabel}
        />
      ) : null}
    </div>
  );
}

export default function ReceptionWorkflowPage() {
  return (
    <AppShell title="Reception order" workspacePath="/app/reception">
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <ReceptionOrderWorkflowPanel />
      </Suspense>
    </AppShell>
  );
}
