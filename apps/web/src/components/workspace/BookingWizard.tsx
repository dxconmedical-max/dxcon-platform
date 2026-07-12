"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, ChevronLeft, ChevronRight, Home, MapPin } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import {
  DataState,
  QrPanel,
  SectionHeader,
} from "@/components/workspace/primitives";
import {
  createBooking,
  fetchCatalog,
  fetchLocations,
  fetchSlots,
  type BookingConfirmation,
  type CatalogItem,
  type ServiceLocation,
  type TimeSlot,
} from "@/lib/api/booking";
import type { DataSource } from "@/lib/api/adapter";
import { normalizeApiError } from "@/lib/errors";

const STEPS = ["Packages", "Location", "Schedule", "Review", "Confirmed"] as const;

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
}

function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}

export function BookingWizard({
  accessToken,
  organizationId,
  defaultContactName,
}: {
  accessToken: string;
  organizationId: string;
  defaultContactName?: string;
}) {
  const ctx = useMemo(
    () => ({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );

  const [step, setStep] = useState(0);

  const [catalog, setCatalog] = useState<CatalogItem[]>([]);
  const [catalogSource, setCatalogSource] = useState<DataSource>("sample");
  const [catalogLoading, setCatalogLoading] = useState(true);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Record<string, CatalogItem>>({});

  const [locations, setLocations] = useState<ServiceLocation[]>([]);
  const [locationSource, setLocationSource] = useState<DataSource>("sample");
  const [locationId, setLocationId] = useState<string | null>(null);
  const [homeCollection, setHomeCollection] = useState(false);
  const [homeAddress, setHomeAddress] = useState("");

  const [date, setDate] = useState(todayISO());
  const [slots, setSlots] = useState<TimeSlot[]>([]);
  const [slotSource, setSlotSource] = useState<DataSource>("sample");
  const [slotLoading, setSlotLoading] = useState(false);
  const [slot, setSlot] = useState<TimeSlot | null>(null);

  const [contactName, setContactName] = useState(defaultContactName ?? "");
  const [contactPhone, setContactPhone] = useState("");

  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<BookingConfirmation | null>(null);
  const [confirmationSource, setConfirmationSource] = useState<DataSource>("sample");

  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let cancelled = false;
    void fetchCatalog(ctx)
      .then((result) => {
        if (cancelled) return;
        setCatalog(result.value);
        setCatalogSource(result.source);
        setCatalogLoading(false);
      })
      .catch((error) => {
        if (cancelled) return;
        setCatalogError(normalizeApiError(error));
        setCatalogLoading(false);
      });
    void fetchLocations(ctx).then((result) => {
      if (cancelled) return;
      setLocations(result.value);
      setLocationSource(result.source);
    });
    return () => {
      cancelled = true;
    };
  }, [ctx, retry]);

  useEffect(() => {
    if (step !== 2) return;
    if (homeCollection && !homeAddress) return;
    if (!homeCollection && !locationId) return;
    let cancelled = false;
    void fetchSlots(ctx, locationId ?? "home", date)
      .then((result) => {
        if (cancelled) return;
        setSlots(result.value);
        setSlotSource(result.source);
        setSlotLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setSlots([]);
        setSlotLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [ctx, step, date, locationId, homeCollection, homeAddress]);

  const selectedItems = Object.values(selected);
  const total = selectedItems.reduce((sum, item) => sum + (item.price ?? 0), 0);

  const canProceed = (() => {
    if (step === 0) return selectedItems.length > 0;
    if (step === 1) return homeCollection ? homeAddress.trim().length > 3 : Boolean(locationId);
    if (step === 2) return Boolean(slot);
    if (step === 3) return contactName.trim().length > 1 && contactPhone.trim().length > 5;
    return false;
  })();

  function toggleItem(item: CatalogItem) {
    setSelected((prev) => {
      const next = { ...prev };
      if (next[item.code]) delete next[item.code];
      else next[item.code] = item;
      return next;
    });
  }

  async function submit() {
    setSubmitting(true);
    setSubmitError(null);
    try {
      const result = await createBooking(ctx, {
        items: selectedItems,
        locationId,
        homeCollection,
        homeAddress: homeCollection ? homeAddress : undefined,
        slot,
        contactName,
        contactPhone,
      });
      setConfirmation(result.value);
      setConfirmationSource(result.source);
      setStep(4);
    } catch (error) {
      setSubmitError(normalizeApiError(error));
    } finally {
      setSubmitting(false);
    }
  }

  function reset() {
    setSelected({});
    setLocationId(null);
    setHomeCollection(false);
    setHomeAddress("");
    setDate(todayISO());
    setSlot(null);
    setContactName(defaultContactName ?? "");
    setContactPhone("");
    setConfirmation(null);
    setSubmitError(null);
    setStep(0);
  }

  return (
    <div className="space-y-6">
      <ol className="flex flex-wrap items-center gap-2 text-sm">
        {STEPS.map((label, index) => {
          const done = index < step;
          const active = index === step;
          return (
            <li key={label} className="flex items-center gap-2">
              <span
                className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-semibold ${
                  active
                    ? "bg-teal-600 text-white"
                    : done
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-slate-100 text-slate-500"
                }`}
              >
                {done ? <Check className="h-4 w-4" /> : index + 1}
              </span>
              <span className={active ? "font-medium text-slate-900" : "text-slate-500"}>{label}</span>
              {index < STEPS.length - 1 ? <span className="text-slate-300">—</span> : null}
            </li>
          );
        })}
      </ol>

      {step === 0 ? (
        <div className="space-y-4">
          <SectionHeader
            title="Select packages & tests"
            description="Choose one or more services for this booking."
            source={catalogSource}
          />
          <DataState
            loading={catalogLoading}
            error={catalogError}
            empty={catalog.length === 0}
            emptyLabel="No catalog items available."
          onRetry={() => {
            setCatalogLoading(true);
            setCatalogError(null);
            setRetry((n) => n + 1);
          }}
        >
          <div className="grid gap-3 md:grid-cols-2">
            {catalog.map((item) => {
                const isSelected = Boolean(selected[item.code]);
                return (
                  <button
                    type="button"
                    key={item.code}
                    onClick={() => toggleItem(item)}
                    className={`flex flex-col rounded-xl border p-4 text-left transition ${
                      isSelected
                        ? "border-teal-500 bg-teal-50/60 ring-1 ring-teal-500/30"
                        : "border-slate-200 bg-white hover:border-teal-300"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-medium text-slate-900">{item.name}</span>
                      {isSelected ? <Check className="h-4 w-4 text-teal-600" /> : null}
                    </div>
                    <div className="mt-1 flex flex-wrap gap-2 text-xs text-slate-500">
                      {item.category ? <Badge>{item.category}</Badge> : null}
                      {item.home_collection ? <Badge tone="info">Home collection</Badge> : null}
                    </div>
                    <div className="mt-3 flex items-center justify-between text-sm">
                      <span className="text-slate-500">
                        {item.turnaround_hours ? `~${item.turnaround_hours}h` : "—"}
                      </span>
                      <span className="font-semibold text-slate-900">
                        {item.price ? formatCurrency(item.price) : "—"}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </DataState>
        </div>
      ) : null}

      {step === 1 ? (
        <div className="space-y-4">
          <SectionHeader
            title="Choose location"
            description="Visit a branch or request home collection."
            source={locationSource}
          />
          <div className="grid gap-3 md:grid-cols-2">
            <button
              type="button"
              onClick={() => setHomeCollection(false)}
              className={`flex items-center gap-3 rounded-xl border p-4 text-left ${
                !homeCollection ? "border-teal-500 bg-teal-50/60" : "border-slate-200 hover:border-teal-300"
              }`}
            >
              <MapPin className="h-5 w-5 text-teal-600" />
              <span className="font-medium text-slate-900">Visit a branch</span>
            </button>
            <button
              type="button"
              onClick={() => setHomeCollection(true)}
              className={`flex items-center gap-3 rounded-xl border p-4 text-left ${
                homeCollection ? "border-teal-500 bg-teal-50/60" : "border-slate-200 hover:border-teal-300"
              }`}
            >
              <Home className="h-5 w-5 text-teal-600" />
              <span className="font-medium text-slate-900">Home collection</span>
            </button>
          </div>

          {homeCollection ? (
            <div>
              <Label htmlFor="home-address">Collection address</Label>
              <Input
                id="home-address"
                value={homeAddress}
                onChange={(event) => setHomeAddress(event.target.value)}
                placeholder="Street, district, city"
              />
            </div>
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {locations.map((location) => (
                <button
                  type="button"
                  key={location.id}
                  onClick={() => setLocationId(location.id)}
                  className={`rounded-xl border p-4 text-left ${
                    locationId === location.id
                      ? "border-teal-500 bg-teal-50/60"
                      : "border-slate-200 hover:border-teal-300"
                  }`}
                >
                  <p className="font-medium text-slate-900">{location.name}</p>
                  <p className="mt-1 text-sm text-slate-500">{location.address}</p>
                  {location.city ? <p className="text-xs text-slate-400">{location.city}</p> : null}
                </button>
              ))}
            </div>
          )}
        </div>
      ) : null}

      {step === 2 ? (
        <div className="space-y-4">
          <SectionHeader
            title="Pick a schedule"
            description="Select a date and available time slot."
            source={slotSource}
          />
          <div className="max-w-xs">
            <Label htmlFor="booking-date">Date</Label>
            <Input
              id="booking-date"
              type="date"
              value={date}
              min={todayISO()}
              onChange={(event) => {
                setDate(event.target.value);
                setSlot(null);
                setSlotLoading(true);
              }}
            />
          </div>
          {slotLoading ? (
            <p className="text-sm text-slate-500">Loading slots…</p>
          ) : (
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
              {slots.map((option) => {
                const disabled = !option.available;
                const active = slot?.id === option.id;
                return (
                  <button
                    type="button"
                    key={option.id}
                    disabled={disabled}
                    onClick={() => setSlot(option)}
                    className={`rounded-lg border px-3 py-2 text-sm ${
                      active
                        ? "border-teal-500 bg-teal-600 text-white"
                        : disabled
                          ? "cursor-not-allowed border-slate-100 bg-slate-50 text-slate-300"
                          : "border-slate-200 text-slate-700 hover:border-teal-400"
                    }`}
                  >
                    {option.time}
                  </button>
                );
              })}
            </div>
          )}
        </div>
      ) : null}

      {step === 3 ? (
        <div className="space-y-4">
          <SectionHeader title="Review & contact" description="Confirm details before booking." />
          <Card className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500">Services</span>
              <span className="text-right font-medium text-slate-900">
                {selectedItems.map((item) => item.name).join(", ")}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500">Location</span>
              <span className="font-medium text-slate-900">
                {homeCollection
                  ? `Home collection — ${homeAddress}`
                  : locations.find((l) => l.id === locationId)?.name ?? "—"}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500">Schedule</span>
              <span className="font-medium text-slate-900">
                {date} {slot?.time}
              </span>
            </div>
            <div className="flex items-center justify-between border-t border-slate-100 pt-3 text-sm">
              <span className="text-slate-500">Total</span>
              <span className="text-lg font-semibold text-slate-900">{formatCurrency(total)}</span>
            </div>
          </Card>
          <div className="grid gap-3 md:grid-cols-2">
            <div>
              <Label htmlFor="contact-name">Contact name</Label>
              <Input
                id="contact-name"
                value={contactName}
                onChange={(event) => setContactName(event.target.value)}
                placeholder="Full name"
              />
            </div>
            <div>
              <Label htmlFor="contact-phone">Contact phone</Label>
              <Input
                id="contact-phone"
                value={contactPhone}
                onChange={(event) => setContactPhone(event.target.value)}
                placeholder="Phone number"
              />
            </div>
          </div>
          {submitError ? (
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800">{submitError}</p>
          ) : null}
        </div>
      ) : null}

      {step === 4 && confirmation ? (
        <div className="space-y-4">
          <SectionHeader
            title="Booking confirmed"
            description="Show this QR code at collection or check-in."
            source={confirmationSource}
          />
          <div className="grid gap-4 md:grid-cols-[auto_1fr] md:items-center">
            <QrPanel payload={confirmation.qrPayload} caption={`Reference ${confirmation.reference}`} />
            <Card className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Reference</span>
                <span className="font-medium text-slate-900">{confirmation.reference}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Scheduled</span>
                <span className="font-medium text-slate-900">{confirmation.scheduled_at}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Location</span>
                <span className="font-medium text-slate-900">{confirmation.location}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Total</span>
                <span className="font-medium text-slate-900">{formatCurrency(confirmation.total)}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">Status</span>
                <Badge tone="success">{confirmation.status}</Badge>
              </div>
            </Card>
          </div>
          <Button variant="outline" onClick={reset}>
            Book another
          </Button>
        </div>
      ) : null}

      {step < 4 ? (
        <div className="flex items-center justify-between border-t border-slate-100 pt-4">
          <Button
            variant="ghost"
            disabled={step === 0}
            onClick={() => setStep((s) => Math.max(0, s - 1))}
          >
            <ChevronLeft className="h-4 w-4" />
            Back
          </Button>
          <div className="flex items-center gap-3">
            {selectedItems.length > 0 ? (
              <span className="text-sm text-slate-500">
                {selectedItems.length} selected · {formatCurrency(total)}
              </span>
            ) : null}
            {step < 3 ? (
              <Button
                disabled={!canProceed}
                onClick={() => {
                  if (step === 1) setSlotLoading(true);
                  setStep((s) => s + 1);
                }}
              >
                Continue
                <ChevronRight className="h-4 w-4" />
              </Button>
            ) : (
              <Button disabled={!canProceed || submitting} onClick={submit}>
                {submitting ? "Booking…" : "Confirm booking"}
              </Button>
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
