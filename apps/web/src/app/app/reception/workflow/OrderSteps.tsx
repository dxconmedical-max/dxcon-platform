"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { DataState, SectionHeader, SimpleTable } from "@/components/workspace/primitives";
import {
  createReceptionOrder,
  fetchReceptionTests,
  getOrderCode,
  registerWalkIn,
  searchReceptionPatients,
  type ReceptionOrderCreate,
  type ReceptionPatient,
  type ReceptionTest,
} from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

export type SelectedPatient = { patientCode: string; patientName: string };

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
}

function asFloat(value: string): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function unique<T>(items: T[]): T[] {
  return Array.from(new Set(items));
}

export function PatientStep({
  accessToken,
  organizationId,
  initialQuery,
  onSelect,
}: {
  accessToken: string;
  organizationId: string;
  initialQuery?: string;
  onSelect: (patient: SelectedPatient) => void;
}) {
  const [query, setQuery] = useState(initialQuery ?? "");
  const [patients, setPatients] = useState<ReceptionPatient[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [create, setCreate] = useState({
    full_name: "",
    phone: "",
    national_id: "",
    gender: "",
    date_of_birth: "",
  });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  async function runSearch(term = query) {
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const result = await searchReceptionPatients(
        { token: accessToken, organizationId },
        term.trim(),
      );
      setPatients(result.items);
    } catch (err) {
      setPatients([]);
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialQuery?.trim()) {
      void runSearch(initialQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery, accessToken, organizationId]);

  async function submitCreate() {
    if (!create.full_name.trim() || !create.phone.trim()) {
      setCreateError("Full name and phone are required.");
      return;
    }
    setCreating(true);
    setCreateError(null);
    try {
      const response = await registerWalkIn(
        { token: accessToken, organizationId },
        {
          full_name: create.full_name.trim(),
          phone: create.phone.trim(),
          national_id: create.national_id.trim() || undefined,
          gender: create.gender.trim() || undefined,
          date_of_birth: create.date_of_birth.trim() || undefined,
        },
      );
      onSelect({
        patientCode: response.value.patient_code,
        patientName: create.full_name.trim(),
      });
    } catch (err) {
      setCreateError(normalizeApiError(err));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-4">
          <SectionHeader
            title="Patient search"
            description="Search by patient code, name, phone, or national ID."
          />
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              void runSearch();
            }}
          >
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Patient code, name, phone, or national ID"
            />
            <Button type="submit" disabled={loading}>
              Search
            </Button>
          </form>

          {searched ? (
            <DataState
              loading={loading}
              error={error}
              empty={patients.length === 0}
              emptyLabel="No patients found. Register a new patient on the right."
              onRetry={() => void runSearch()}
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
                          onSelect({ patientCode: row.patient_code, patientName: row.full_name })
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
              Search for an existing patient or register a walk-in.
            </p>
          )}
        </div>

        <Card className="space-y-4">
          <SectionHeader title="Create new patient" description="Walk-in registration." />
          <div className="grid gap-4 md:grid-cols-2">
            <div>
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
              <Label htmlFor="national_id">National ID</Label>
              <Input
                id="national_id"
                value={create.national_id}
                onChange={(event) => setCreate((prev) => ({ ...prev, national_id: event.target.value }))}
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
            <div className="md:col-span-2">
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
          </div>
          {createError ? <p className="text-sm text-rose-600">{createError}</p> : null}
          <Button onClick={() => void submitCreate()} disabled={creating}>
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
  organizationId: string;
  patient: SelectedPatient;
  onOrderCreated: (orderRef: string, pricing: ReceptionOrderCreate["pricing"]) => void;
}) {
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tests, setTests] = useState<ReceptionTest[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTestIds, setSelectedTestIds] = useState<string[]>([]);
  const [discount, setDiscount] = useState("0");
  const [note, setNote] = useState("");

  const categories = useMemo(
    () => unique(tests.map((test) => test.category).filter(Boolean) as string[]).sort(),
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
  const subtotal = useMemo(
    () => selectedTests.reduce((sum, test) => sum + (test.price ?? 0), 0),
    [selectedTests],
  );
  const total = Math.max(0, subtotal - asFloat(discount));

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    void fetchReceptionTests({ token: accessToken, organizationId }, { limit: 100 })
      .then((result) => {
        if (!cancelled) setTests(result.items);
      })
      .catch((err) => {
        if (!cancelled) {
          setTests([]);
          setError(normalizeApiError(err));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, organizationId]);

  function toggleCategory(category: string) {
    const ids = categoryToTestIds[category] ?? [];
    const isSelected = selectedCategories.includes(category);
    setSelectedCategories((prev) =>
      isSelected ? prev.filter((value) => value !== category) : [...prev, category],
    );
    setSelectedTestIds((prev) =>
      isSelected ? prev.filter((id) => !ids.includes(id)) : unique([...prev, ...ids]),
    );
  }

  async function submitOrder() {
    setCreating(true);
    setError(null);
    try {
      const response = await createReceptionOrder(
        { token: accessToken, organizationId },
        {
          patient_code: patient.patientCode,
          test_catalog_ids: selectedTestIds,
          discount: asFloat(discount),
          note: note.trim() || undefined,
        },
      );
      const orderRef = getOrderCode(response.order);
      if (!orderRef) throw new Error("Order code not returned by the API.");
      onOrderCreated(orderRef, response.pricing);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Select tests & create order"
        description={`${patient.patientName} · ${patient.patientCode}`}
      />
      <DataState
        loading={loading}
        error={error}
        empty={!loading && tests.length === 0}
        emptyLabel="No tests found in master data."
        onRetry={() => window.location.reload()}
      >
        <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
          <Card className="space-y-3">
            <p className="text-sm font-medium text-slate-900">Test packages</p>
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
                <p className="text-lg font-semibold text-slate-900">{selectedTestIds.length} tests</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-600">Estimated total</p>
                <p className="font-semibold text-slate-900">{formatCurrency(total)}</p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="discount">Discount</Label>
                <Input id="discount" value={discount} onChange={(event) => setDiscount(event.target.value)} />
              </div>
              <div>
                <Label htmlFor="note">Note</Label>
                <Input id="note" value={note} onChange={(event) => setNote(event.target.value)} />
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
                      onChange={() =>
                        setSelectedTestIds((prev) =>
                          prev.includes(row.id)
                            ? prev.filter((id) => id !== row.id)
                            : [...prev, row.id],
                        )
                      }
                    />
                  ),
                },
                { key: "code", label: "Code", render: (row) => row.code },
                { key: "name", label: "Test", render: (row) => row.name },
                { key: "category", label: "Package", render: (row) => row.category ?? "—" },
                {
                  key: "price",
                  label: "Price",
                  render: (row) => (row.price != null ? formatCurrency(row.price) : "—"),
                },
              ]}
            />

            <Button disabled={creating || selectedTestIds.length === 0} onClick={() => void submitOrder()}>
              {creating ? "Creating order…" : "Create order"}
            </Button>
          </div>
        </div>
      </DataState>
    </div>
  );
}

export { formatCurrency };
