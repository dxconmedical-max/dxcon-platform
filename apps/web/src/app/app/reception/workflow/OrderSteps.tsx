"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import {
  collectReceptionPayment,
  createReceptionOrder,
  fetchReceptionBarcodes,
  fetchReceptionLabHandoff,
  fetchReceptionOrder,
  fetchReceptionPatient,
  fetchReceptionRequestForm,
  fetchReceptionTests,
  getDuplicateWarnings,
  getOrderCode,
  handoffReceptionOrderToLab,
  isValidPatientQr,
  registerWalkIn,
  searchReceptionPatients,
  RECEPTION_LAB_HANDOFF_TIMEOUT_MS,
  RECEPTION_PAYMENT_METHODS,
  RECEPTION_PAYMENT_TIMEOUT_MS,
  type DuplicateWarning,
  type ReceptionBarcodes,
  type ReceptionLabHandoff,
  type ReceptionOrderCreate,
  type ReceptionOrderPricing,
  type ReceptionPaymentRecord,
  type ReceptionPaymentSummary,
  type ReceptionPatient,
  type ReceptionTest,
} from "@/lib/api/reception";
import { isRequestAborted, normalizeApiError } from "@/lib/errors";

import { DataState, SectionHeader, SimpleTable } from "../_components/ui";

export type SelectedPatient = {
  patientCode: string;
  patientName: string;
};

const SEARCH_DEBOUNCE_MS = 350;

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
}

function asFloat(value: string): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function uniqueIds(items: string[]): string[] {
  return Array.from(new Set(items));
}

export function PatientStep({
  accessToken,
  organizationId,
  initialQuery,
  preservedQuery,
  onSelect,
  onQueryChange,
}: {
  accessToken: string;
  organizationId?: string | null;
  initialQuery?: string;
  preservedQuery?: string;
  onSelect: (patient: SelectedPatient) => void;
  onQueryChange?: (query: string) => void;
}) {
  const [query, setQuery] = useState(preservedQuery ?? initialQuery ?? "");
  const [patients, setPatients] = useState<ReceptionPatient[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(Boolean((preservedQuery ?? initialQuery)?.trim()));
  const [error, setError] = useState<string | null>(null);
  const [create, setCreate] = useState({
    full_name: "",
    phone: "",
    national_id: "",
    gender: "",
    date_of_birth: "",
    email: "",
    address: "",
    patient_code: "",
  });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [duplicates, setDuplicates] = useState<DuplicateWarning[]>([]);
  const searchAbortRef = useRef<AbortController | null>(null);
  const createInFlight = useRef(false);

  async function runSearch(term: string, opts?: { immediate?: boolean }) {
    const q = term.trim();
    searchAbortRef.current?.abort();
    const controller = new AbortController();
    searchAbortRef.current = controller;
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const result = await searchReceptionPatients(
        {
          token: accessToken,
          organizationId,
          signal: controller.signal,
          timeoutMs: 30_000,
        },
        q,
      );
      if (controller.signal.aborted) return;
      setPatients(result.items);
    } catch (err) {
      if (isRequestAborted(err) || controller.signal.aborted) return;
      setPatients([]);
      setError(normalizeApiError(err));
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
    void opts;
  }

  useEffect(() => {
    onQueryChange?.(query);
  }, [query, onQueryChange]);

  useEffect(() => {
    const term = query.trim();
    if (!term) {
      searchAbortRef.current?.abort();
      return;
    }
    const timer = window.setTimeout(() => {
      void runSearch(term);
    }, SEARCH_DEBOUNCE_MS);
    return () => {
      window.clearTimeout(timer);
      searchAbortRef.current?.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, accessToken, organizationId]);

  useEffect(() => {
    if (initialQuery?.trim() && !preservedQuery && initialQuery !== query) {
      const timer = window.setTimeout(() => setQuery(initialQuery), 0);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [initialQuery, preservedQuery, query]);

  async function submitCreate(force = false) {
    if (createInFlight.current) return;
    if (!create.full_name.trim() || !create.phone.trim()) {
      setCreateError("Full name and phone are required.");
      return;
    }
    createInFlight.current = true;
    setCreating(true);
    setCreateError(null);
    if (!force) setDuplicates([]);
    try {
      if (!force && (create.phone.trim() || create.national_id.trim())) {
        const probe = await searchReceptionPatients(
          { token: accessToken, organizationId },
          create.phone.trim() || create.national_id.trim(),
        );
        const matches = probe.items.filter(
          (p) =>
            (create.phone.trim() && p.phone === create.phone.trim()) ||
            (create.national_id.trim() && p.national_id === create.national_id.trim()),
        );
        if (matches.length > 0) {
          setDuplicates(
            matches.map((p) => ({
              patient_code: p.patient_code,
              full_name: p.full_name,
              phone: p.phone ?? undefined,
              national_id: p.national_id ?? undefined,
              message: `Existing patient ${p.full_name}`,
            })),
          );
          setCreateError("Possible duplicate patient. Review matches or register anyway.");
          return;
        }
      }

      const response = await registerWalkIn(
        { token: accessToken, organizationId, timeoutMs: 30_000 },
        {
          full_name: create.full_name.trim(),
          phone: create.phone.trim(),
          national_id: create.national_id.trim() || undefined,
          gender: create.gender.trim() || undefined,
          date_of_birth: create.date_of_birth.trim() || undefined,
          email: create.email.trim() || undefined,
          address: create.address.trim() || undefined,
          patient_code: create.patient_code.trim() || undefined,
          force,
        },
      );

      const confirmed = await fetchReceptionPatient(
        { token: accessToken, organizationId },
        response.patient_code,
      );

      setDuplicates([]);
      onSelect({
        patientCode: confirmed.patient_code,
        patientName: confirmed.full_name,
      });
    } catch (err) {
      const warnings = getDuplicateWarnings(err);
      if (warnings.length > 0) {
        setDuplicates(warnings);
        setCreateError("Possible duplicate patient. Review matches below or register anyway.");
      } else {
        setCreateError(normalizeApiError(err));
      }
    } finally {
      createInFlight.current = false;
      setCreating(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-4">
          <SectionHeader
            title="Patient search"
            description="Search by phone, patient code, national ID, or full name."
          />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Phone, patient code, national ID, or name"
            aria-label="Patient search"
          />
          <p className="text-xs text-slate-500">Results update as you type (debounced).</p>

          {searched ? (
            <DataState
              loading={loading}
              error={error}
              empty={!loading && patients.length === 0}
              emptyLabel="No patients found. Register a new patient on the right."
              onRetry={() => void runSearch(query)}
            >
              <SimpleTable<ReceptionPatient>
                rows={patients}
                rowKey={(row) => row.patient_code}
                columns={[
                  { key: "code", label: "Code", render: (row) => row.patient_code },
                  { key: "name", label: "Name", render: (row) => row.full_name },
                  { key: "phone", label: "Phone", render: (row) => row.phone ?? "—" },
                  { key: "nid", label: "National ID", render: (row) => row.national_id ?? "—" },
                  {
                    key: "action",
                    label: "",
                    render: (row) => (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          onSelect({
                            patientCode: row.patient_code,
                            patientName: row.full_name,
                          })
                        }
                      >
                        Select
                      </Button>
                    ),
                  },
                ]}
              />
            </DataState>
          ) : (
            <p className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
              Type to search an existing patient or register a walk-in.
            </p>
          )}
        </div>

        <Card className="space-y-4">
          <SectionHeader
            title="Create new patient"
            description="Walk-in registration with duplicate detection. Search results stay visible."
          />
          <div className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2">
              <Label htmlFor="full_name">Full name *</Label>
              <Input
                id="full_name"
                value={create.full_name}
                onChange={(event) => setCreate((prev) => ({ ...prev, full_name: event.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="phone">Phone *</Label>
              <Input
                id="phone"
                value={create.phone}
                onChange={(event) => setCreate((prev) => ({ ...prev, phone: event.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="patient_code">Patient code (optional)</Label>
              <Input
                id="patient_code"
                value={create.patient_code}
                onChange={(event) =>
                  setCreate((prev) => ({ ...prev, patient_code: event.target.value }))
                }
              />
            </div>
            <div>
              <Label htmlFor="national_id">National ID</Label>
              <Input
                id="national_id"
                value={create.national_id}
                onChange={(event) =>
                  setCreate((prev) => ({ ...prev, national_id: event.target.value }))
                }
              />
            </div>
            <div>
              <Label htmlFor="gender">Gender</Label>
              <Input
                id="gender"
                value={create.gender}
                onChange={(event) => setCreate((prev) => ({ ...prev, gender: event.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="dob">Date of birth</Label>
              <Input
                id="dob"
                type="date"
                value={create.date_of_birth}
                onChange={(event) =>
                  setCreate((prev) => ({ ...prev, date_of_birth: event.target.value }))
                }
              />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={create.email}
                onChange={(event) => setCreate((prev) => ({ ...prev, email: event.target.value }))}
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="address">Address</Label>
              <Input
                id="address"
                value={create.address}
                onChange={(event) => setCreate((prev) => ({ ...prev, address: event.target.value }))}
              />
            </div>
          </div>
          {createError ? <p className="text-sm text-rose-600">{createError}</p> : null}
          {duplicates.length > 0 ? (
            <div className="space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-3">
              <p className="text-sm font-medium text-amber-900">Duplicate detection</p>
              <ul className="space-y-2 text-sm text-amber-900">
                {duplicates.map((warning, index) => (
                  <li
                    key={`${warning.patient_code ?? warning.field ?? "dup"}-${index}`}
                    className="flex flex-wrap items-center justify-between gap-2"
                  >
                    <span>
                      {String(warning.message ?? warning.reason ?? "Possible match")}
                      {warning.patient_code ? ` (${warning.patient_code})` : ""}
                    </span>
                    {warning.patient_code ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          onSelect({
                            patientCode: String(warning.patient_code),
                            patientName: String(warning.full_name ?? warning.patient_code),
                          })
                        }
                      >
                        Use existing
                      </Button>
                    ) : null}
                  </li>
                ))}
              </ul>
              <Button
                variant="secondary"
                disabled={creating}
                onClick={() => void submitCreate(true)}
              >
                {creating ? "Registering…" : "Register anyway"}
              </Button>
            </div>
          ) : null}
          <Button onClick={() => void submitCreate(false)} disabled={creating}>
            {creating ? "Registering…" : "Register & continue"}
          </Button>
        </Card>
      </div>
    </div>
  );
}

export function TestsStep({
  accessToken,
  organizationId,
  patient,
  onOrderCreated,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  onOrderCreated: (
    orderRef: string,
    pricing: ReceptionOrderPricing,
    order: ReceptionOrderCreate["order"],
  ) => void;
}) {
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalogQuery, setCatalogQuery] = useState("");
  const [tests, setTests] = useState<ReceptionTest[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTestIds, setSelectedTestIds] = useState<string[]>([]);
  const [discount, setDiscount] = useState("0");
  const [note, setNote] = useState("");
  const [collectionMode, setCollectionMode] = useState<
    "AT_RECEPTION" | "HOME_COLLECTION" | "CLINIC_COLLECTION"
  >("AT_RECEPTION");
  const [pickupAddress, setPickupAddress] = useState("");
  const [pickupCity, setPickupCity] = useState("");
  const [contactPhone, setContactPhone] = useState("");
  const [requestedDate, setRequestedDate] = useState("");
  const [timeWindow, setTimeWindow] = useState("");
  const catalogAbortRef = useRef<AbortController | null>(null);
  const createInFlight = useRef(false);

  const categories = useMemo(
    () =>
      Array.from(new Set(tests.map((test) => test.category).filter(Boolean) as string[])).sort(),
    [tests],
  );
  const categoryToTestIds = useMemo(() => {
    const map: Record<string, string[]> = {};
    for (const test of tests) {
      if (!test.category) continue;
      map[test.category] = map[test.category] ?? [];
      map[test.category].push(test.id);
    }
    return map;
  }, [tests]);

  const selectedTests = useMemo(
    () => tests.filter((test) => selectedTestIds.includes(test.id)),
    [tests, selectedTestIds],
  );
  const previewSubtotal = useMemo(
    () => selectedTests.reduce((sum, test) => sum + (test.price ?? 0), 0),
    [selectedTests],
  );
  const previewTotal = Math.max(0, previewSubtotal - asFloat(discount));

  async function loadCatalog(q?: string) {
    catalogAbortRef.current?.abort();
    const controller = new AbortController();
    catalogAbortRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchReceptionTests(
        { token: accessToken, organizationId, signal: controller.signal },
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

  function toggleCategory(category: string) {
    const ids = categoryToTestIds[category] ?? [];
    const isSelected = selectedCategories.includes(category);
    setSelectedCategories((prev) =>
      isSelected ? prev.filter((value) => value !== category) : [...prev, category],
    );
    setSelectedTestIds((prev) =>
      isSelected ? prev.filter((id) => !ids.includes(id)) : uniqueIds([...prev, ...ids]),
    );
  }

  function toggleTest(id: string) {
    setSelectedTestIds((prev) =>
      prev.includes(id) ? prev.filter((value) => value !== id) : uniqueIds([...prev, id]),
    );
  }

  async function submitOrder() {
    if (createInFlight.current) return;
    if (selectedTestIds.length === 0) {
      setError("Select at least one test.");
      return;
    }
    if (collectionMode !== "AT_RECEPTION") {
      if (!pickupAddress.trim() || !pickupCity.trim() || !contactPhone.trim() || !requestedDate || !timeWindow.trim()) {
        setError("Field collection requires address, city, phone, date, and time window.");
        return;
      }
    }
    createInFlight.current = true;
    setCreating(true);
    setError(null);
    try {
      const response = await createReceptionOrder(
        { token: accessToken, organizationId, timeoutMs: 30_000 },
        {
          patient_code: patient.patientCode,
          test_catalog_ids: uniqueIds(selectedTestIds),
          discount: asFloat(discount),
          note: note.trim() || undefined,
          collection_mode: collectionMode,
          pickup_address: collectionMode === "AT_RECEPTION" ? undefined : pickupAddress.trim(),
          pickup_city: collectionMode === "AT_RECEPTION" ? undefined : pickupCity.trim(),
          contact_phone: collectionMode === "AT_RECEPTION" ? undefined : contactPhone.trim(),
          requested_date: collectionMode === "AT_RECEPTION" ? undefined : requestedDate,
          requested_time_window: collectionMode === "AT_RECEPTION" ? undefined : timeWindow.trim(),
        },
      );
      const orderRef = getOrderCode(response.order);
      if (!orderRef) throw new Error("Order code not returned by the API.");
      onOrderCreated(orderRef, response.pricing, response.order);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      createInFlight.current = false;
      setCreating(false);
    }
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Select tests & create order"
        description={`${patient.patientName} · ${patient.patientCode}`}
      />
      <Input
        value={catalogQuery}
        onChange={(event) => setCatalogQuery(event.target.value)}
        placeholder="Search test catalog"
        aria-label="Catalog search"
      />
      <DataState
        loading={loading}
        error={error}
        empty={!loading && tests.length === 0}
        emptyLabel="No tests found in master data."
        onRetry={() => void loadCatalog(catalogQuery)}
      >
        <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
          <Card className="space-y-3">
            <p className="text-sm font-medium text-slate-900">Packages (by category)</p>
            <p className="text-xs text-slate-500">
              Backend has no panel expansion — selecting a package adds its catalog tests.
            </p>
            {categories.length === 0 ? (
              <p className="text-sm text-slate-500">No packages available.</p>
            ) : (
              categories.map((category) => (
                <label
                  key={category}
                  className="flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm"
                >
                  <span className="min-w-0 truncate">{category}</span>
                  <input
                    type="checkbox"
                    checked={selectedCategories.includes(category)}
                    onChange={() => toggleCategory(category)}
                  />
                </label>
              ))
            )}
          </Card>

          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3">
              <div>
                <p className="text-sm text-slate-600">Selected</p>
                <p className="text-lg font-semibold text-slate-900">
                  {selectedTestIds.length} tests
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-600">Preview (not final)</p>
                <p className="font-semibold text-slate-900">{formatCurrency(previewTotal)}</p>
                <p className="text-xs text-slate-500">
                  Authoritative totals come from the API after create.
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="discount">Discount</Label>
                <Input
                  id="discount"
                  value={discount}
                  onChange={(event) => setDiscount(event.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="note">Note</Label>
                <Input id="note" value={note} onChange={(event) => setNote(event.target.value)} />
              </div>
            </div>

            <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-medium text-slate-900">Collection method</p>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={collectionMode}
                onChange={(e) =>
                  setCollectionMode(
                    e.target.value as "AT_RECEPTION" | "HOME_COLLECTION" | "CLINIC_COLLECTION",
                  )
                }
                aria-label="Collection method"
              >
                <option value="AT_RECEPTION">At reception (desk)</option>
                <option value="HOME_COLLECTION">Home collection</option>
                <option value="CLINIC_COLLECTION">Clinic collection</option>
              </select>
              <p className="text-xs text-slate-500">
                Route:{" "}
                {collectionMode === "AT_RECEPTION"
                  ? "Reception desk worklist → lab handover"
                  : "Field collector queue → transport → lab arrival"}
              </p>
              {collectionMode !== "AT_RECEPTION" ? (
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="md:col-span-2">
                    <Label htmlFor="pickup-address">Pickup address</Label>
                    <Input
                      id="pickup-address"
                      value={pickupAddress}
                      onChange={(e) => setPickupAddress(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="pickup-city">City / province</Label>
                    <Input id="pickup-city" value={pickupCity} onChange={(e) => setPickupCity(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="contact-phone">Contact phone</Label>
                    <Input
                      id="contact-phone"
                      value={contactPhone}
                      onChange={(e) => setContactPhone(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="req-date">Requested date</Label>
                    <Input
                      id="req-date"
                      type="date"
                      value={requestedDate}
                      onChange={(e) => setRequestedDate(e.target.value)}
                    />
                  </div>
                  <div>
                    <Label htmlFor="time-window">Time window</Label>
                    <Input
                      id="time-window"
                      placeholder="e.g. 08:00–10:00"
                      value={timeWindow}
                      onChange={(e) => setTimeWindow(e.target.value)}
                    />
                  </div>
                </div>
              ) : null}
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
                      onChange={() => toggleTest(row.id)}
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
                { key: "category", label: "Package", render: (row) => row.category ?? "—" },
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
                  <button
                    key={test.id}
                    type="button"
                    className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs text-slate-700 hover:border-rose-300 hover:text-rose-700"
                    onClick={() => toggleTest(test.id)}
                  >
                    {test.code} ×
                  </button>
                ))}
              </div>
            ) : null}

            <Button
              disabled={creating || selectedTestIds.length === 0}
              onClick={() => void submitOrder()}
            >
              {creating ? "Creating order…" : "Create order"}
            </Button>
          </div>
        </div>
      </DataState>
    </div>
  );
}


export function OrderCreatedStep(props: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  orderRef: string;
  pricing: ReceptionOrderPricing;
  order: ReceptionOrderCreate["order"];
  onReset: () => void;
  cashierLabel?: string | null;
}) {
  return <PaymentStep {...props} />;
}

export function PaymentStep({
  accessToken,
  organizationId,
  patient,
  orderRef,
  pricing,
  order,
  onReset,
  cashierLabel,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  orderRef: string;
  pricing: ReceptionOrderPricing;
  order: ReceptionOrderCreate["order"];
  onReset: () => void;
  cashierLabel?: string | null;
}) {
  const [authoritative, setAuthoritative] = useState(pricing);
  const [detail, setDetail] = useState(order);
  const [summary, setSummary] = useState<ReceptionPaymentSummary>(() => ({
    order_total: pricing.total,
    paid_amount: 0,
    outstanding_amount: pricing.total,
    discount: pricing.discount,
    subtotal: pricing.subtotal,
    tax: pricing.tax ?? null,
    status: "unpaid",
    payment_methods_supported: [...RECEPTION_PAYMENT_METHODS],
    partial_payments_supported: true,
  }));
  const [payment, setPayment] = useState<ReceptionPaymentRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState("cash");
  const [amountInput, setAmountInput] = useState(String(pricing.total));
  const [showDocuments, setShowDocuments] = useState(false);
  const [idempotencyKey, setIdempotencyKey] = useState(() =>
    typeof crypto !== "undefined" && crypto.randomUUID
      ? `pay-${crypto.randomUUID()}`
      : `pay-${Date.now()}`,
  );
  const submitLock = useRef(false);

  const items = Array.isArray((detail as { items?: unknown }).items)
    ? ((detail as { items: Record<string, unknown>[] }).items ?? [])
    : [];
  const methods =
    summary.payment_methods_supported?.length
      ? summary.payment_methods_supported
      : [...RECEPTION_PAYMENT_METHODS];
  const isPaid = summary.status === "paid" || summary.outstanding_amount <= 0;

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const orderResult = await fetchReceptionOrder(
        { token: accessToken, organizationId },
        orderRef,
        { patientCode: patient.patientCode },
      );
      setAuthoritative(orderResult.pricing);
      setDetail(orderResult.order);
      if (orderResult.payment_summary) {
        setSummary(orderResult.payment_summary);
        setAmountInput(String(orderResult.payment_summary.outstanding_amount));
      }
      if (orderResult.payment) setPayment(orderResult.payment);
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

  function validateAmount(raw: string, outstanding: number, allowPartial: boolean): number {
    const value = Number(raw);
    if (!Number.isFinite(value)) throw new Error("Enter a valid payment amount.");
    if (value <= 0) throw new Error("Payment amount must be greater than zero.");
    if (value > outstanding + 0.0001) {
      throw new Error(`Overpayment not allowed. Outstanding is ${formatCurrency(outstanding)}.`);
    }
    if (!allowPartial && value + 0.0001 < outstanding) {
      throw new Error(
        "Partial payments are not supported. Amount must equal the outstanding balance.",
      );
    }
    return value;
  }

  async function submitPayment() {
    if (submitLock.current || paying) return;
    setError(null);
    let amount: number;
    try {
      amount = validateAmount(
        amountInput,
        summary.outstanding_amount,
        Boolean(summary.partial_payments_supported),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid amount");
      return;
    }
    submitLock.current = true;
    setPaying(true);
    try {
      const result = await collectReceptionPayment(
        { token: accessToken, organizationId, timeoutMs: RECEPTION_PAYMENT_TIMEOUT_MS },
        orderRef,
        { payment_method: paymentMethod, amount, idempotency_key: idempotencyKey },
      );
      setSummary(result.payment_summary);
      setPayment(result.payment);
      if (result.payment_summary.status !== "paid") {
        setIdempotencyKey(
          typeof crypto !== "undefined" && crypto.randomUUID
            ? `pay-${crypto.randomUUID()}`
            : `pay-${Date.now()}`,
        );
        setAmountInput(String(result.payment_summary.outstanding_amount));
      }
      await refresh();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setPaying(false);
      submitLock.current = false;
    }
  }

  function openPrintableReceipt() {
    if (!payment) return;
    const paidAt = payment.paid_at ? new Date(payment.paid_at).toLocaleString() : "—";
    const cashier = cashierLabel || payment.created_by || "—";
    const html = `<!doctype html><html><head><title>Receipt ${escapeHtml(payment.receipt_number)}</title>
<style>body{font-family:ui-monospace,Menlo,monospace;padding:24px}.row{display:flex;justify-content:space-between;margin:6px 0;font-size:13px}.hr{border-top:1px dashed #94a3b8;margin:12px 0}</style></head><body>
<h1>DxCon Reception Receipt</h1>
<div class="row"><span>Receipt</span><span>${escapeHtml(payment.receipt_number)}</span></div>
<div class="row"><span>Order</span><span>${escapeHtml(orderRef)}</span></div>
<div class="row"><span>Patient</span><span>${escapeHtml(patient.patientName)} (${escapeHtml(patient.patientCode)})</span></div>
<div class="hr"></div>
<div class="row"><span>Method</span><span>${escapeHtml(payment.payment_method)}</span></div>
<div class="row"><span>Amount</span><span>${escapeHtml(formatCurrency(payment.amount))}</span></div>
<div class="row"><span>Status</span><span>${escapeHtml(summary.status)}</span></div>
<div class="row"><span>Paid at</span><span>${escapeHtml(paidAt)}</span></div>
<div class="row"><span>Cashier</span><span>${escapeHtml(cashier)}</span></div>
<script>window.onload=function(){window.print()}</script></body></html>`;
    const popup = window.open("", "_blank", "noopener,noreferrer,width=480,height=720");
    if (!popup) return;
    popup.document.write(html);
    popup.document.close();
  }

  if (showDocuments && isPaid) {
    return (
      <DocumentsStep
        accessToken={accessToken}
        organizationId={organizationId}
        patient={patient}
        orderRef={orderRef}
        pricing={authoritative}
        payment={payment}
        cashierLabel={cashierLabel}
        onReset={onReset}
        onBackToPayment={() => setShowDocuments(false)}
      />
    );
  }

  return (
    <div className="space-y-5">
      <Card className="space-y-4">
        <SectionHeader
          title="Payment & receipt"
          description="Collect payment against the authoritative backend total. Documents unlock after paid status."
          actions={
            <Button size="sm" variant="outline" disabled={loading} onClick={() => void refresh()}>
              {loading ? "Refreshing…" : "Refresh"}
            </Button>
          }
        />
        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            <p>{error}</p>
            <Button className="mt-2" size="sm" variant="outline" onClick={() => void refresh()}>
              Retry
            </Button>
          </div>
        ) : null}
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Patient</p>
            <p className="font-medium text-slate-900">{patient.patientName}</p>
            <p className="text-xs text-slate-500">{patient.patientCode}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Order total</p>
            <p className="font-semibold text-slate-900">{formatCurrency(summary.order_total)}</p>
            <p className="text-xs text-slate-500">
              Subtotal {formatCurrency(summary.subtotal ?? authoritative.subtotal)} · Discount{" "}
              {formatCurrency(summary.discount ?? authoritative.discount)}
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Paid / outstanding</p>
            <p className="font-semibold text-slate-900">{formatCurrency(summary.paid_amount)}</p>
            <p className="text-xs text-slate-500">Due {formatCurrency(summary.outstanding_amount)}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Order · status</p>
            <p className="break-all font-mono text-sm">{orderRef}</p>
            <p className="text-xs font-medium uppercase text-slate-600">{summary.status}</p>
          </div>
        </div>
        {items.length > 0 ? (
          <SimpleTable
            rows={items}
            rowKey={(row, index) => String(row.id ?? row.test_code ?? index)}
            columns={[
              { key: "code", label: "Code", render: (row) => String(row.test_code ?? "—") },
              { key: "name", label: "Test", render: (row) => String(row.test_name ?? "—") },
              {
                key: "price",
                label: "Unit price",
                render: (row) =>
                  row.unit_price != null ? formatCurrency(Number(row.unit_price)) : "—",
              },
            ]}
          />
        ) : null}
      </Card>

      {!isPaid ? (
        <Card className="space-y-4">
          <SectionHeader
            title="Settle outstanding balance"
            description="Full settlement only. Amount must equal outstanding."
          />
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="payment_method">Payment method</Label>
              <select
                id="payment_method"
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                value={paymentMethod}
                onChange={(event) => setPaymentMethod(event.target.value)}
                disabled={paying}
              >
                {methods.map((method) => (
                  <option key={method} value={method}>
                    {method}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="pay_amount">Amount due</Label>
              <Input
                id="pay_amount"
                inputMode="decimal"
                value={amountInput}
                onChange={(event) => setAmountInput(event.target.value)}
                disabled={paying}
              />
            </div>
          </div>
          <Button disabled={paying || loading} onClick={() => void submitPayment()}>
            {paying ? "Recording payment…" : "Collect payment"}
          </Button>
        </Card>
      ) : (
        <Card className="space-y-4">
          <SectionHeader title="Receipt" description="Payment persisted from the backend." />
          {payment ? (
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Receipt / reference</p>
                <p className="font-mono text-sm">{payment.receipt_number}</p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Date / time</p>
                <p className="text-sm">
                  {payment.paid_at ? new Date(payment.paid_at).toLocaleString() : "—"}
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Method</p>
                <p className="text-sm">{payment.payment_method}</p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Amount</p>
                <p className="text-sm font-semibold">{formatCurrency(payment.amount)}</p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Cashier</p>
                <p className="text-sm">{cashierLabel || payment.created_by || "—"}</p>
              </div>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" disabled={!payment} onClick={openPrintableReceipt}>
              Print receipt
            </Button>
            <Button onClick={() => setShowDocuments(true)}>Continue to barcodes & requisition</Button>
            <Button variant="ghost" onClick={onReset}>
              New order
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}

export function DocumentsStep({
  accessToken,
  organizationId,
  patient,
  orderRef,
  pricing,
  payment,
  cashierLabel,
  onReset,
  onBackToPayment,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  orderRef: string;
  pricing: ReceptionOrderPricing;
  payment: ReceptionPaymentRecord | null;
  cashierLabel?: string | null;
  onReset: () => void;
  onBackToPayment?: () => void;
}) {
  const [barcodes, setBarcodes] = useState<ReceptionBarcodes | null>(null);
  const [requisitionHtml, setRequisitionHtml] = useState<string | null>(null);
  const [handoff, setHandoff] = useState<ReceptionLabHandoff | null>(null);
  const [loading, setLoading] = useState(false);
  const [handingOff, setHandingOff] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [handoffError, setHandoffError] = useState<string | null>(null);
  const handoffLock = useRef(false);

  const documentsReady = Boolean(
    barcodes?.order_barcode &&
      (barcodes.sample_barcodes?.length ?? 0) > 0 &&
      (requisitionHtml || "").trim(),
  );
  const alreadyHandedOff = Boolean(
    handoff?.handed_off ||
      handoff?.order_status === "lab_received" ||
      handoff?.order_status === "testing",
  );

  async function loadDocuments() {
    setLoading(true);
    setError(null);
    try {
      const [codes, form, status] = await Promise.all([
        fetchReceptionBarcodes({ token: accessToken, organizationId }, orderRef),
        fetchReceptionRequestForm({ token: accessToken, organizationId }, orderRef),
        fetchReceptionLabHandoff(
          { token: accessToken, organizationId, timeoutMs: RECEPTION_LAB_HANDOFF_TIMEOUT_MS },
          orderRef,
        ).catch(() => null),
      ]);
      if (!isValidPatientQr(codes.patient_qr)) {
        throw new Error("Invalid patient QR payload from backend.");
      }
      setBarcodes(codes);
      setRequisitionHtml(form.html);
      if (status?.handed_off) {
        setHandoff(status);
      }
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadDocuments();
    }, 0);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderRef, accessToken, organizationId]);

  async function submitHandoff() {
    if (handoffLock.current || handingOff || alreadyHandedOff || !documentsReady) return;
    handoffLock.current = true;
    setHandingOff(true);
    setHandoffError(null);
    try {
      const result = await handoffReceptionOrderToLab(
        { token: accessToken, organizationId, timeoutMs: RECEPTION_LAB_HANDOFF_TIMEOUT_MS },
        orderRef,
      );
      setHandoff(result);
      const refreshed = await fetchReceptionLabHandoff(
        { token: accessToken, organizationId, timeoutMs: RECEPTION_LAB_HANDOFF_TIMEOUT_MS },
        orderRef,
      );
      setHandoff(refreshed);
    } catch (err) {
      setHandoffError(normalizeApiError(err));
    } finally {
      setHandingOff(false);
      handoffLock.current = false;
    }
  }

  function openLabels() {
    if (!barcodes) return;
    const sampleRows = (barcodes.sample_barcodes || [])
      .map(
        (s) => `<div class="label"><div><strong>${escapeHtml(s.barcode)}</strong></div>
<div>${escapeHtml(patient.patientName)} · ${escapeHtml(patient.patientCode)}</div>
<div>${escapeHtml(orderRef)} · ${escapeHtml(s.test_code)}</div>
<div>${escapeHtml(s.sample_type || s.test_name)}</div>
<div>${escapeHtml(s.collection_requirement || "Standard collection")}</div>
<div>${escapeHtml(barcodes.generated_at || "")}</div></div>`,
      )
      .join("");
    const html = `<!doctype html><html><head><title>Labels ${escapeHtml(orderRef)}</title>
<style>
body{font-family:ui-monospace,Menlo,monospace;padding:16px}
.label{border:1px solid #0f172a;padding:12px;margin:0 0 12px;width:320px;page-break-inside:avoid;font-size:12px}
</style></head><body>
<div class="label"><div><strong>${escapeHtml(barcodes.order_barcode)}</strong></div>
<div>Order ${escapeHtml(orderRef)}</div>
<div>${escapeHtml(patient.patientName)} (${escapeHtml(patient.patientCode)})</div>
<div>QR ${escapeHtml(barcodes.patient_qr)}</div>
<div>${escapeHtml(barcodes.generated_at || "")}</div></div>
${sampleRows}
<script>window.onload=function(){window.print()}</script></body></html>`;
    const popup = window.open("", "_blank", "noopener,noreferrer,width=420,height=720");
    if (!popup) return;
    popup.document.write(html);
    popup.document.close();
  }

  function openRequisition() {
    if (!requisitionHtml) return;
    const popup = window.open("", "_blank", "noopener,noreferrer");
    if (!popup) return;
    popup.document.write(requisitionHtml);
    popup.document.close();
  }

  return (
    <div className="space-y-5">
      <Card className="space-y-4">
        <SectionHeader
          title="Barcode, QR & requisition"
          description="Backend-generated identifiers for the paid order. Reprint returns the same codes."
          actions={
            <Button size="sm" variant="outline" disabled={loading} onClick={() => void loadDocuments()}>
              {loading ? "Loading…" : barcodes?.reprint ? "Reprint / refresh" : "Generate / refresh"}
            </Button>
          }
        />
        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            <p>{error}</p>
            <Button className="mt-2" size="sm" variant="outline" onClick={() => void loadDocuments()}>
              Retry
            </Button>
          </div>
        ) : null}
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Order</p>
            <p className="font-mono text-sm">{orderRef}</p>
            <p className="text-xs text-slate-500">Total {formatCurrency(pricing.total)}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Patient</p>
            <p className="font-medium">{patient.patientName}</p>
            <p className="text-xs text-slate-500">{patient.patientCode}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Receipt</p>
            <p className="font-mono text-sm">{payment?.receipt_number ?? "—"}</p>
            <p className="text-xs text-slate-500">{cashierLabel || payment?.created_by || "—"}</p>
          </div>
        </div>
      </Card>

      {barcodes ? (
        <Card className="space-y-4">
          <SectionHeader
            title="Identifiers"
            description={
              barcodes.reprint
                ? "Reprint — same backend identifiers (no new codes created)."
                : "First generation — identifiers persisted for this order."
            }
          />
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-slate-200 p-3">
              <p className="text-xs text-slate-500">Order barcode</p>
              <p className="font-mono text-sm">{barcodes.order_barcode}</p>
            </div>
            <div className="rounded-lg border border-slate-200 p-3">
              <p className="text-xs text-slate-500">Patient barcode</p>
              <p className="font-mono text-sm">{barcodes.patient_barcode}</p>
            </div>
            <div className="rounded-lg border border-slate-200 p-3 md:col-span-2">
              <p className="text-xs text-slate-500">Patient QR payload</p>
              <p className="break-all font-mono text-sm">{barcodes.patient_qr}</p>
              <p className="mt-1 text-xs text-emerald-700">
                {isValidPatientQr(barcodes.patient_qr) ? "QR format valid" : "Invalid QR format"}
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 p-3">
              <p className="text-xs text-slate-500">Generated at</p>
              <p className="text-sm">
                {barcodes.generated_at
                  ? new Date(barcodes.generated_at).toLocaleString()
                  : "—"}
              </p>
            </div>
          </div>
          {barcodes.sample_barcodes?.length ? (
            <SimpleTable
              rows={barcodes.sample_barcodes}
              rowKey={(row, index) => `${row.barcode}-${index}`}
              columns={[
                { key: "specimen", label: "Specimen", render: (row) => row.specimen_code ?? "—" },
                { key: "barcode", label: "Barcode", render: (row) => row.barcode },
                { key: "test", label: "Test", render: (row) => `${row.test_code} · ${row.test_name}` },
                { key: "type", label: "Type", render: (row) => row.sample_type ?? "—" },
              ]}
            />
          ) : null}
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={openLabels}>
              Print labels
            </Button>
            <Button variant="outline" disabled={!requisitionHtml} onClick={openRequisition}>
              Open requisition
            </Button>
            <Button variant="ghost" onClick={() => void loadDocuments()}>
              Reprint
            </Button>
          </div>
        </Card>
      ) : loading ? (
        <p className="text-sm text-slate-500">Generating identifiers…</p>
      ) : null}

      {documentsReady ? (
        <Card className="space-y-4">
          <SectionHeader
            title="Laboratory handoff"
            description="Send this paid, documented order into the laboratory incoming queue once."
          />
          {handoffError ? (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              <p>{handoffError}</p>
              <Button
                className="mt-2"
                size="sm"
                variant="outline"
                disabled={handingOff || alreadyHandedOff}
                onClick={() => void submitHandoff()}
              >
                Retry handoff
              </Button>
            </div>
          ) : null}
          {alreadyHandedOff ? (
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
                <p className="text-xs text-emerald-700">Accepted at</p>
                <p className="text-sm text-emerald-900">
                  {handoff?.accepted_at ? new Date(handoff.accepted_at).toLocaleString() : "—"}
                </p>
              </div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
                <p className="text-xs text-emerald-700">Order / sample status</p>
                <p className="text-sm font-medium uppercase text-emerald-900">
                  {handoff?.order_status ?? "—"}
                  {handoff?.collection?.status
                    ? ` · ${String(handoff.collection.status)}`
                    : ""}
                </p>
              </div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
                <p className="text-xs text-emerald-700">Destination laboratory</p>
                <p className="text-sm text-emerald-900">
                  {handoff?.laboratory.name ?? "Central Laboratory"}
                </p>
              </div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
                <p className="text-xs text-emerald-700">Queue reference</p>
                <p className="font-mono text-sm text-emerald-900">
                  {handoff?.queue_reference ?? "—"}
                </p>
              </div>
            </div>
          ) : (
            <Button
              disabled={handingOff || !documentsReady}
              onClick={() => void submitHandoff()}
            >
              {handingOff ? "Handing off…" : "Hand off to Laboratory"}
            </Button>
          )}
          {alreadyHandedOff ? (
            <p className="text-xs text-slate-500">
              Handoff is complete. Repeat submit is disabled; refresh reloads persisted status.
            </p>
          ) : null}
        </Card>
      ) : null}

      <div className="flex flex-wrap gap-3">
        {onBackToPayment ? (
          <Button variant="outline" onClick={onBackToPayment}>
            Back to receipt
          </Button>
        ) : null}
        <Button onClick={onReset}>New order</Button>
        <a href={`/app/reception/workflow?order=${encodeURIComponent(orderRef)}`}>
          <Button variant="ghost">Reopen order link</Button>
        </a>
      </div>
    </div>
  );
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export { formatCurrency };
