"use client";

/**
 * Reception Milestone 1 — Patient, catalog, authoritative pricing, order confirmation.
 * Does not implement payment, barcode, QR, requisition, or lab handoff.
 */

import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import {
  createReceptionOrder,
  fetchReceptionOrder,
  fetchReceptionTests,
  getOrderCode,
  type ReceptionOrderCreate,
  type ReceptionOrderPricing,
  type ReceptionTest,
} from "@/lib/api/reception";
import { isRequestAborted, normalizeApiError } from "@/lib/errors";

import { DataState, SectionHeader, SimpleTable } from "../_components/ui";
import { PatientStep, type SelectedPatient } from "./OrderSteps";

const SEARCH_DEBOUNCE_MS = 400;

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
}

function asFloat(value: string): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function uniqueIds(items: string[]): string[] {
  return Array.from(new Set(items.filter(Boolean)));
}

export type CatalogSelection = {
  testIds: string[];
  tests: ReceptionTest[];
  discount: number;
  note: string;
  estimateSubtotal: number;
  estimateTotal: number;
};

export type CollectionRequestDraft = {
  mode: "AT_RECEPTION" | "HOME_COLLECTION" | "CLINIC_COLLECTION";
  specimen_type: string;
  pickup_address?: string;
  pickup_province?: string;
  pickup_district?: string;
  pickup_ward?: string;
  contact_person?: string;
  contact_phone?: string;
  requested_date?: string;
  requested_time_window?: string;
  notes?: string;
  priority?: string;
  clinic_name?: string;
};

export function collectionModeLabel(mode: CollectionRequestDraft["mode"]): string {
  if (mode === "AT_RECEPTION") return "DESK (at reception)";
  if (mode === "HOME_COLLECTION") return "HOME collection";
  return "CLINIC collection";
}

export function CollectionRequestStep({
  patient,
  selection,
  initial,
  onContinue,
  onBack,
}: {
  patient: SelectedPatient;
  selection: CatalogSelection;
  initial?: CollectionRequestDraft | null;
  onContinue: (draft: CollectionRequestDraft) => void;
  onBack: () => void;
}) {
  const defaultSpecimen =
    selection.tests.map((t) => t.sample_type).find((s) => s && s.trim() && s.toLowerCase() !== "consult") ||
    "BLOOD";
  const [mode, setMode] = useState<CollectionRequestDraft["mode"]>(initial?.mode ?? "AT_RECEPTION");
  const [specimenType, setSpecimenType] = useState(initial?.specimen_type || String(defaultSpecimen));
  const [pickupAddress, setPickupAddress] = useState(initial?.pickup_address ?? "");
  const [province, setProvince] = useState(initial?.pickup_province ?? "");
  const [district, setDistrict] = useState(initial?.pickup_district ?? "");
  const [ward, setWard] = useState(initial?.pickup_ward ?? "");
  const [contactPerson, setContactPerson] = useState(initial?.contact_person ?? patient.patientName);
  const [contactPhone, setContactPhone] = useState(initial?.contact_phone ?? "");
  const [requestedDate, setRequestedDate] = useState(initial?.requested_date ?? "");
  const [timeWindow, setTimeWindow] = useState(initial?.requested_time_window ?? "");
  const [notes, setNotes] = useState(initial?.notes ?? "");
  const [priority, setPriority] = useState(initial?.priority ?? "ROUTINE");
  const [clinicName, setClinicName] = useState(initial?.clinic_name ?? "");
  const [error, setError] = useState<string | null>(null);

  function submit() {
    setError(null);
    if (!specimenType.trim()) {
      setError("Specimen type is required.");
      return;
    }
    if (mode === "HOME_COLLECTION") {
      if (
        !pickupAddress.trim() ||
        !province.trim() ||
        !district.trim() ||
        !contactPerson.trim() ||
        !contactPhone.trim() ||
        !requestedDate ||
        !timeWindow.trim()
      ) {
        setError(
          "HOME collection requires address, province, district, contact person, phone, date, and time window.",
        );
        return;
      }
    }
    if (mode === "CLINIC_COLLECTION") {
      if (!clinicName.trim() || !requestedDate || !timeWindow.trim()) {
        setError("CLINIC collection requires clinic, preferred date, and preferred time.");
        return;
      }
    }
    onContinue({
      mode,
      specimen_type: specimenType.trim(),
      pickup_address: mode === "HOME_COLLECTION" ? pickupAddress.trim() : undefined,
      pickup_province: mode === "HOME_COLLECTION" ? province.trim() : undefined,
      pickup_district: mode === "HOME_COLLECTION" ? district.trim() : undefined,
      pickup_ward: mode === "HOME_COLLECTION" ? ward.trim() || undefined : undefined,
      contact_person:
        mode === "HOME_COLLECTION" ? contactPerson.trim() : mode === "CLINIC_COLLECTION" ? contactPerson.trim() || undefined : undefined,
      contact_phone: mode === "HOME_COLLECTION" ? contactPhone.trim() : undefined,
      requested_date: mode === "AT_RECEPTION" ? undefined : requestedDate,
      requested_time_window: mode === "AT_RECEPTION" ? undefined : timeWindow.trim(),
      notes: notes.trim() || undefined,
      priority: mode === "AT_RECEPTION" ? undefined : priority,
      clinic_name: mode === "CLINIC_COLLECTION" ? clinicName.trim() : undefined,
    });
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Collection request"
        description="Choose how the specimen will be collected before pricing and order creation."
        actions={
          <Button size="sm" variant="outline" onClick={onBack}>
            Back
          </Button>
        }
      />
      <Card className="space-y-4">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs text-slate-500">Patient</p>
          <p className="font-medium">{patient.patientName}</p>
          <p className="font-mono text-xs text-slate-500">{patient.patientCode}</p>
        </div>

        <div>
          <Label htmlFor="collection-mode">Collection mode</Label>
          <select
            id="collection-mode"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            value={mode}
            onChange={(e) => setMode(e.target.value as CollectionRequestDraft["mode"])}
          >
            <option value="AT_RECEPTION">DESK (at reception)</option>
            <option value="HOME_COLLECTION">HOME</option>
            <option value="CLINIC_COLLECTION">CLINIC</option>
          </select>
          <p className="mt-1 text-xs text-slate-500">
            {mode === "AT_RECEPTION"
              ? "Creates a reception desk SampleCollection only — not a field collector job."
              : mode === "HOME_COLLECTION"
                ? "Creates a field collection request (PENDING_ASSIGNMENT) for the HOME collector queue."
                : "Creates a CLINIC pickup request on Field Collection Requests (not the HOME collector queue)."}
          </p>
        </div>

        <div>
          <Label htmlFor="specimen-type">Specimen type</Label>
          <Input
            id="specimen-type"
            value={specimenType}
            onChange={(e) => setSpecimenType(e.target.value)}
            placeholder="e.g. BLOOD"
          />
        </div>

        {mode === "HOME_COLLECTION" ? (
          <div className="grid gap-3 md:grid-cols-2">
            <div className="md:col-span-2">
              <Label htmlFor="pickup-address">Pickup address *</Label>
              <Input id="pickup-address" value={pickupAddress} onChange={(e) => setPickupAddress(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="province">Province *</Label>
              <Input id="province" value={province} onChange={(e) => setProvince(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="district">District *</Label>
              <Input id="district" value={district} onChange={(e) => setDistrict(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="ward">Ward</Label>
              <Input id="ward" value={ward} onChange={(e) => setWard(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="contact-person">Contact person *</Label>
              <Input id="contact-person" value={contactPerson} onChange={(e) => setContactPerson(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="contact-phone">Phone *</Label>
              <Input id="contact-phone" value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="req-date">Preferred date *</Label>
              <Input id="req-date" type="date" value={requestedDate} onChange={(e) => setRequestedDate(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="time-window">Preferred time window *</Label>
              <Input
                id="time-window"
                placeholder="e.g. 08:00–10:00"
                value={timeWindow}
                onChange={(e) => setTimeWindow(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="priority">Priority</Label>
              <select
                id="priority"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="ROUTINE">ROUTINE</option>
                <option value="URGENT">URGENT</option>
                <option value="STAT">STAT</option>
              </select>
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="home-notes">Notes</Label>
              <Input id="home-notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
            </div>
          </div>
        ) : null}

        {mode === "CLINIC_COLLECTION" ? (
          <div className="grid gap-3 md:grid-cols-2">
            <div className="md:col-span-2">
              <Label htmlFor="clinic-name">Clinic *</Label>
              <Input id="clinic-name" value={clinicName} onChange={(e) => setClinicName(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="clinic-date">Preferred date *</Label>
              <Input id="clinic-date" type="date" value={requestedDate} onChange={(e) => setRequestedDate(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="clinic-time">Preferred time *</Label>
              <Input
                id="clinic-time"
                placeholder="e.g. 09:00"
                value={timeWindow}
                onChange={(e) => setTimeWindow(e.target.value)}
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="clinic-notes">Notes</Label>
              <Input id="clinic-notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
            </div>
          </div>
        ) : null}

        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        <Button onClick={submit}>Continue to pricing</Button>
      </Card>
    </div>
  );
}

export function CatalogSelectStep({
  accessToken,
  organizationId,
  patient,
  initial,
  onContinue,
  onBack,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  initial?: CatalogSelection | null;
  onContinue: (selection: CatalogSelection) => void;
  onBack: () => void;
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [catalogQuery, setCatalogQuery] = useState("");
  const [tests, setTests] = useState<ReceptionTest[]>([]);
  const [selectedTests, setSelectedTests] = useState<ReceptionTest[]>(initial?.tests ?? []);
  const [discount, setDiscount] = useState(String(initial?.discount ?? 0));
  const [note, setNote] = useState(initial?.note ?? "");
  const catalogAbortRef = useRef<AbortController | null>(null);

  const selectedTestIds = useMemo(() => selectedTests.map((test) => test.id), [selectedTests]);
  const estimateSubtotal = useMemo(
    () => selectedTests.reduce((sum, test) => sum + (test.price ?? 0), 0),
    [selectedTests],
  );
  const estimateTotal = Math.max(0, estimateSubtotal - asFloat(discount));

  async function loadCatalog(q?: string) {
    catalogAbortRef.current?.abort();
    const controller = new AbortController();
    catalogAbortRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchReceptionTests(
        { token: accessToken, organizationId, signal: controller.signal, timeoutMs: 30_000 },
        { limit: 100, q: q?.trim() || undefined },
      );
      if (controller.signal.aborted) return;
      setTests(result.items);
    } catch (err) {
      if (isRequestAborted(err) || controller.signal.aborted) return;
      setTests([]);
      setError(normalizeApiError(err));
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadCatalog(catalogQuery);
    }, catalogQuery ? SEARCH_DEBOUNCE_MS : 0);
    return () => {
      window.clearTimeout(timer);
      catalogAbortRef.current?.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalogQuery, accessToken, organizationId]);

  function toggleTest(row: ReceptionTest) {
    setSelectedTests((prev) => {
      if (prev.some((test) => test.id === row.id)) {
        return prev.filter((test) => test.id !== row.id);
      }
      return [...prev.filter((test) => test.id !== row.id), row];
    });
  }

  function continueNext() {
    if (selectedTests.length === 0) {
      setError("Select at least one test.");
      return;
    }
    onContinue({
      testIds: uniqueIds(selectedTestIds),
      tests: selectedTests,
      discount: asFloat(discount),
      note: note.trim(),
      estimateSubtotal,
      estimateTotal,
    });
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Select tests"
        description={`${patient.patientName} · ${patient.patientCode}. Catalog prices are display estimates until order creation.`}
        actions={
          <Button size="sm" variant="outline" onClick={onBack}>
            Back
          </Button>
        }
      />
      <Input
        value={catalogQuery}
        onChange={(event) => setCatalogQuery(event.target.value)}
        placeholder="Search test catalog by code or name"
        aria-label="Catalog search"
      />
      <DataState
        loading={loading}
        error={error}
        empty={!loading && tests.length === 0}
        emptyLabel="No tests found in master data."
        onRetry={() => void loadCatalog(catalogQuery)}
      >
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="m1-discount">Discount (estimate)</Label>
              <Input
                id="m1-discount"
                value={discount}
                onChange={(event) => setDiscount(event.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="m1-note">Note</Label>
              <Input id="m1-note" value={note} onChange={(event) => setNote(event.target.value)} />
            </div>
          </div>
          <SimpleTable<ReceptionTest>
            rows={tests}
            rowKey={(row) => row.id}
            columns={[
              {
                key: "pick",
                label: "",
                render: (row) => (
                  <input
                    type="checkbox"
                    checked={selectedTestIds.includes(row.id)}
                    onChange={() => toggleTest(row)}
                    aria-label={`Select ${row.code}`}
                  />
                ),
              },
              { key: "code", label: "Code", render: (row) => row.code },
              { key: "name", label: "Test", render: (row) => row.name },
              {
                key: "specimen",
                label: "Specimen",
                render: (row) => row.sample_type ?? "—",
              },
              {
                key: "tat",
                label: "TAT (h)",
                render: (row) =>
                  row.turnaround_hours != null ? String(row.turnaround_hours) : "—",
              },
              {
                key: "price",
                label: "Catalog price",
                render: (row) => (row.price != null ? formatCurrency(row.price) : "—"),
              },
            ]}
          />
          {selectedTests.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {selectedTests.map((test) => (
                <Button
                  key={test.id}
                  size="sm"
                  variant="outline"
                  onClick={() => toggleTest(test)}
                  aria-label={`Remove ${test.code}`}
                >
                  {test.code} ×
                </Button>
              ))}
            </div>
          ) : null}
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm">
            <p>
              Selected {selectedTests.length} · Estimate subtotal{" "}
              {formatCurrency(estimateSubtotal)} · Estimate total {formatCurrency(estimateTotal)}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Estimate only — final totals come from the order create response.
            </p>
          </div>
          <Button disabled={selectedTests.length === 0} onClick={continueNext}>
            Review pricing
          </Button>
        </div>
      </DataState>
    </div>
  );
}

export function ReviewPricingStep({
  accessToken,
  organizationId,
  patient,
  selection,
  collectionRequest,
  onBack,
  onCreated,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  selection: CatalogSelection;
  collectionRequest: CollectionRequestDraft;
  onBack: () => void;
  onCreated: (result: {
    orderRef: string;
    pricing: ReceptionOrderPricing;
    order: ReceptionOrderCreate["order"];
    invoice: ReceptionOrderCreate["invoice"];
  }) => void;
}) {
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [priceDrift, setPriceDrift] = useState<string | null>(null);
  const [pendingResult, setPendingResult] = useState<{
    orderRef: string;
    pricing: ReceptionOrderPricing;
    order: ReceptionOrderCreate["order"];
    invoice: ReceptionOrderCreate["invoice"];
  } | null>(null);
  const inFlight = useRef(false);

  function acceptCreated(result: {
    orderRef: string;
    pricing: ReceptionOrderPricing;
    order: ReceptionOrderCreate["order"];
    invoice: ReceptionOrderCreate["invoice"];
  }) {
    setPendingResult(null);
    setPriceDrift(null);
    onCreated(result);
  }

  async function submitOrder() {
    if (inFlight.current || pendingResult) return;
    if (!patient.patientCode) {
      setError("Select a patient before creating an order.");
      return;
    }
    if (selection.testIds.length === 0) {
      setError("Select at least one test.");
      return;
    }
    inFlight.current = true;
    setCreating(true);
    setError(null);
    setPriceDrift(null);
    try {
      const response = await createReceptionOrder(
        { token: accessToken, organizationId, timeoutMs: 30_000 },
        {
          patient_code: patient.patientCode,
          test_catalog_ids: uniqueIds(selection.testIds),
          discount: selection.discount,
          note: selection.note || undefined,
          collection_mode: collectionRequest.mode,
          specimen_type: collectionRequest.specimen_type,
          pickup_address: collectionRequest.pickup_address,
          pickup_province: collectionRequest.pickup_province,
          pickup_district: collectionRequest.pickup_district,
          pickup_ward: collectionRequest.pickup_ward,
          contact_person: collectionRequest.contact_person,
          contact_phone: collectionRequest.contact_phone,
          requested_date: collectionRequest.requested_date,
          requested_time_window: collectionRequest.requested_time_window,
          clinic_name: collectionRequest.clinic_name,
          priority: collectionRequest.priority,
          collection_note: collectionRequest.notes,
        },
      );
      const orderRef = getOrderCode(response.order);
      if (!orderRef) {
        throw new Error("Order code not returned by the API.");
      }
      const result = {
        orderRef,
        pricing: response.pricing,
        order: response.order,
        invoice: response.invoice,
      };
      const authoritative = response.pricing.total;
      if (Math.abs(authoritative - selection.estimateTotal) > 0.01) {
        setPendingResult(result);
        setPriceDrift(
          `Backend total ${formatCurrency(authoritative)} differs from estimate ${formatCurrency(selection.estimateTotal)}. Confirm to continue with the backend total.`,
        );
        return;
      }
      acceptCreated(result);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      inFlight.current = false;
      setCreating(false);
    }
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Review and pricing"
        description="Confirm selection and collection route, then create the laboratory order. Backend pricing is authoritative."
        actions={
          <Button size="sm" variant="outline" disabled={creating} onClick={onBack}>
            Back
          </Button>
        }
      />
      <Card className="space-y-4">
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Patient</p>
            <p className="font-medium">{patient.patientName}</p>
            <p className="font-mono text-xs text-slate-500">{patient.patientCode}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Collection route</p>
            <p className="font-medium">{collectionModeLabel(collectionRequest.mode)}</p>
            <p className="text-xs text-slate-500">
              Specimen: {collectionRequest.specimen_type}
              {collectionRequest.mode === "HOME_COLLECTION"
                ? ` · ${collectionRequest.pickup_address || ""}`
                : collectionRequest.mode === "CLINIC_COLLECTION"
                  ? ` · ${collectionRequest.clinic_name || ""}`
                  : " · Reception desk"}
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Display estimate (not final)</p>
            <p className="font-semibold">{formatCurrency(selection.estimateTotal)}</p>
            <p className="text-xs text-slate-500">
              Subtotal {formatCurrency(selection.estimateSubtotal)} · Discount{" "}
              {formatCurrency(selection.discount)}
            </p>
          </div>
        </div>
        <SimpleTable<ReceptionTest>
          rows={selection.tests}
          rowKey={(row) => row.id}
          columns={[
            { key: "code", label: "Code", render: (row) => row.code },
            { key: "name", label: "Test", render: (row) => row.name },
            {
              key: "price",
              label: "Catalog price",
              render: (row) => (row.price != null ? formatCurrency(row.price) : "—"),
            },
          ]}
        />
        {selection.note ? (
          <p className="text-sm text-slate-600">
            Note: <span className="text-slate-900">{selection.note}</span>
          </p>
        ) : null}
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        {priceDrift && pendingResult ? (
          <div className="space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-3">
            <p className="text-sm text-amber-900">{priceDrift}</p>
            <p className="font-mono text-sm text-amber-950">
              Order {pendingResult.orderRef} ·{" "}
              {formatCurrency(pendingResult.pricing.total)}
            </p>
            <Button onClick={() => acceptCreated(pendingResult)}>
              Confirm backend total
            </Button>
          </div>
        ) : null}
        <Button disabled={creating || Boolean(pendingResult)} onClick={() => void submitOrder()}>
          {creating ? "Creating order…" : "Create laboratory order"}
        </Button>
      </Card>
    </div>
  );
}

export function OrderConfirmationStep({
  accessToken,
  organizationId,
  patient,
  orderRef,
  pricing,
  order,
  onCreateAnother,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  orderRef: string;
  pricing: ReceptionOrderPricing;
  order: ReceptionOrderCreate["order"];
  onCreateAnother: () => void;
}) {
  const [detail, setDetail] = useState(order);
  const [authoritative, setAuthoritative] = useState(pricing);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchReceptionOrder(
        { token: accessToken, organizationId, timeoutMs: 30_000 },
        orderRef,
        { patientCode: patient.patientCode },
      );
      setDetail(result.order);
      setAuthoritative(result.pricing);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refresh();
    }, 0);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderRef, accessToken, organizationId]);

  const status = String(detail.status ?? order.status ?? "—");

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Order confirmation"
        description="Backend-issued order number and authoritative pricing. Payment is out of scope for Milestone 1."
        actions={
          <Button size="sm" variant="outline" disabled={loading} onClick={() => void refresh()}>
            {loading ? "Refreshing…" : "Refresh"}
          </Button>
        }
      />
      <Card className="space-y-4">
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
          <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">
            Laboratory order number
          </p>
          <p className="mt-1 break-all font-mono text-lg font-semibold text-emerald-950">
            {orderRef}
          </p>
        </div>
        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            <p>{error}</p>
            <Button className="mt-2" size="sm" variant="outline" onClick={() => void refresh()}>
              Retry
            </Button>
          </div>
        ) : null}
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Patient</p>
            <p className="font-medium">{patient.patientName}</p>
            <p className="font-mono text-xs">{patient.patientCode}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Status</p>
            <p className="font-medium uppercase">{status}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Authoritative total</p>
            <p className="font-semibold">{formatCurrency(authoritative.total)}</p>
            <p className="text-xs text-slate-500">
              Subtotal {formatCurrency(authoritative.subtotal)} · Discount{" "}
              {formatCurrency(authoritative.discount)}
              {authoritative.tax != null ? ` · Tax ${formatCurrency(authoritative.tax)}` : ""}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <a href={`/app/reception/workflow?order=${encodeURIComponent(orderRef)}`}>
            <Button variant="outline">Open order</Button>
          </a>
          <Button onClick={onCreateAnother}>Create another order</Button>
        </div>
      </Card>
    </div>
  );
}

// Re-export PatientStep for workflow composition
export { PatientStep };
export type { SelectedPatient };
