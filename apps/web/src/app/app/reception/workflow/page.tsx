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
  CatalogSelectStep,
  CollectionRequestStep,
  OrderConfirmationStep,
  PatientStep,
  ReviewPricingStep,
  type CatalogSelection,
  type CollectionRequestDraft,
  type SelectedPatient,
} from "./Milestone1Steps";

const STEPS = [
  "Patient",
  "Tests",
  "Collection request",
  "Review and pricing",
  "Confirmation",
] as const;

function ReceptionMilestone1Panel() {
  const { accessToken, activeOrganizationId, can, role } = useAuth();
  const searchParams = useSearchParams();
  const patientParam = searchParams.get("patient") ?? undefined;
  const orderParam = searchParams.get("order") ?? undefined;

  /** UI steps: 0 Patient, 1 Tests, 2 Collection request, 3 Review (create), 4 Confirmation. */
  const [step, setStep] = useState(0);
  const [patient, setPatient] = useState<SelectedPatient | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selection, setSelection] = useState<CatalogSelection | null>(null);
  const [collectionRequest, setCollectionRequest] = useState<CollectionRequestDraft | null>(null);
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

  const badgeIndex = step;

  useEffect(() => {
    if (!orderParam || !accessToken) {
      return;
    }
    let cancelled = false;
    const timer = window.setTimeout(() => {
      if (cancelled) return;
      setReopening(true);
      setReopenError(null);
      void fetchReceptionOrder(
        { token: accessToken, organizationId: activeOrganizationId, timeoutMs: 30_000 },
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
          setStep(4);
        })
        .catch((err) => {
          if (!cancelled) setReopenError(normalizeApiError(err));
        })
        .finally(() => {
          if (!cancelled) setReopening(false);
        });
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [orderParam, accessToken, activeOrganizationId]);

  function reset() {
    setStep(0);
    setPatient(null);
    setSelection(null);
    setCollectionRequest(null);
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
        Reception write permission is required for patient and order workflows.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Reception — Patient, tests, collection request & order"
        description="Record the specimen collection request before pricing and order creation."
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

      <div className="flex flex-wrap gap-2" aria-label="Reception order steps">
        {STEPS.map((label, index) => {
          const active = index === badgeIndex;
          const done = index < badgeIndex;
          return (
            <Badge key={label} tone={active ? "info" : done ? "success" : "default"}>
              {index + 1}. {label}
            </Badge>
          );
        })}
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
        <CatalogSelectStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          initial={selection}
          onBack={() => setStep(0)}
          onContinue={(next) => {
            setSelection(next);
            setStep(2);
          }}
        />
      ) : null}

      {!reopening && step === 2 && patient && selection ? (
        <CollectionRequestStep
          patient={patient}
          selection={selection}
          initial={collectionRequest}
          onBack={() => setStep(1)}
          onContinue={(draft) => {
            setCollectionRequest(draft);
            setStep(3);
          }}
        />
      ) : null}

      {!reopening && step === 3 && patient && selection && collectionRequest ? (
        <ReviewPricingStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          selection={selection}
          collectionRequest={collectionRequest}
          onBack={() => setStep(2)}
          onCreated={({ orderRef: ref, pricing: nextPricing, order: nextOrder }) => {
            setOrderRef(ref);
            setPricing(nextPricing);
            setOrder(nextOrder);
            setStep(4);
          }}
        />
      ) : null}

      {!reopening && step === 4 && patient && orderRef && pricing && order ? (
        <OrderConfirmationStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          orderRef={orderRef}
          pricing={pricing}
          order={order}
          onCreateAnother={reset}
        />
      ) : null}
    </div>
  );
}

export default function ReceptionWorkflowPage() {
  return (
    <AppShell title="Reception order" workspacePath="/app/reception">
      <Suspense fallback={<p className="text-sm text-slate-500">Loading…</p>}>
        <ReceptionMilestone1Panel />
      </Suspense>
    </AppShell>
  );
}
