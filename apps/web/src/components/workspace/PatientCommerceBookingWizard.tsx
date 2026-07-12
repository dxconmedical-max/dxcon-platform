"use client";

import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Home, MapPin, Stethoscope } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { QrPanel, SectionHeader } from "@/components/workspace/primitives";
import {
  fetchPublicPartners,
  fetchPublicServices,
  fetchProviderSlots,
  fetchQuotation,
  type MarketplaceListing,
  type MarketplacePartner,
  type MarketplaceSlot,
} from "@/lib/api/marketplace";
import { apiRequest } from "@/lib/api/client";

const STEPS = [
  "Patient",
  "Service",
  "Provider",
  "Date",
  "Collection",
  "Review",
  "Payment",
  "Confirmed",
] as const;

function formatCurrency(value: number) {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
}

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export function PatientCommerceBookingWizard({
  accessToken,
  organizationId,
  defaultContactName,
  initialListingId,
  initialProviderId,
}: {
  accessToken: string;
  organizationId: string;
  defaultContactName?: string;
  initialListingId?: string;
  initialProviderId?: string;
}) {
  const [step, setStep] = useState(0);
  const [patientName, setPatientName] = useState(defaultContactName ?? "");
  const [services, setServices] = useState<MarketplaceListing[]>([]);
  const [partners, setPartners] = useState<MarketplacePartner[]>([]);
  const [selectedListing, setSelectedListing] = useState<MarketplaceListing | null>(null);
  const [selectedPartner, setSelectedPartner] = useState<MarketplacePartner | null>(null);
  const [date, setDate] = useState(todayISO());
  const [slots, setSlots] = useState<MarketplaceSlot[]>([]);
  const [slot, setSlot] = useState<MarketplaceSlot | null>(null);
  const [collectionType, setCollectionType] = useState<"LAB" | "CLINIC" | "HOME">("LAB");
  const [homeAddress, setHomeAddress] = useState("");
  const [building, setBuilding] = useState("");
  const [collectorNotes, setCollectorNotes] = useState("");
  const [quotation, setQuotation] = useState<{ total_amount: number; pricing_snapshot_id: string } | null>(null);
  const [paymentQr, setPaymentQr] = useState<string | null>(null);
  const [bookingRef, setBookingRef] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    void fetchPublicServices({}).then((r) => {
      setServices(r.value.listings);
      if (initialListingId) {
        const found = r.value.listings.find((s) => s.id === initialListingId);
        if (found) setSelectedListing(found);
      }
    });
    void fetchPublicPartners({}).then((r) => {
      setPartners(r.value.partners);
      if (initialProviderId) {
        const found = r.value.partners.find((p) => p.id === initialProviderId);
        if (found) setSelectedPartner(found);
      }
    });
  }, [initialListingId, initialProviderId]);

  useEffect(() => {
    if (step === 3 && selectedPartner) {
      void fetchProviderSlots(selectedPartner.id, date, organizationId).then((r) => setSlots(r.value.slots));
    }
  }, [step, selectedPartner, date, organizationId]);

  useEffect(() => {
    if (step === 5 && selectedListing) {
      void fetchQuotation(selectedListing.id).then((r) => setQuotation(r.value));
    }
  }, [step, selectedListing]);

  const canProceed = (() => {
    if (step === 0) return patientName.trim().length > 1;
    if (step === 1) return Boolean(selectedListing);
    if (step === 2) return Boolean(selectedPartner);
    if (step === 3) return Boolean(slot);
    if (step === 4) return collectionType !== "HOME" || homeAddress.trim().length > 5;
    if (step === 5) return Boolean(quotation);
    return true;
  })();

  async function createBookingAndPay() {
    if (!selectedListing || !selectedPartner) return;
    setBusy(true);
    try {
      const booking = await apiRequest<{ booking_code?: string; id?: string }>("/api/v1/marketplace/v2/bookings", {
        token: accessToken,
        organizationId,
        method: "POST",
        headers: { "X-Organization-Id": organizationId },
        body: {
          listing_id: selectedListing.id,
          provider_id: selectedPartner.id,
          scheduled_start: slot?.slot_start,
          appointment_type: collectionType === "HOME" ? "HOME_COLLECTION" : "IN_PERSON",
          pickup_address: collectionType === "HOME" ? `${homeAddress} ${building}`.trim() : undefined,
          contact_phone: "",
          pricing_snapshot_id: quotation?.pricing_snapshot_id,
          patient_name: patientName,
        },
      });
      const bookingId = booking.id ?? "";
      setBookingRef(booking.booking_code ?? bookingId);
      const payment = await apiRequest<{ qr_payload?: string }>("/api/v1/marketplace/v2/payments/qr", {
        token: accessToken,
        organizationId,
        method: "POST",
        headers: { "X-Organization-Id": organizationId },
        body: { booking_id: bookingId },
      });
      setPaymentQr(payment.qr_payload ?? bookingRef);
      setStep(7);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <ol className="flex flex-wrap gap-2 text-xs sm:text-sm">
        {STEPS.map((label, i) => (
          <li key={label} className={`rounded-full px-2 py-1 ${i === step ? "bg-teal-600 text-white" : "bg-slate-100 text-slate-500"}`}>
            {i + 1}. {label}
          </li>
        ))}
      </ol>

      {step === 0 && (
        <div>
          <Label htmlFor="patient">Who is this booking for?</Label>
          <Input id="patient" value={patientName} onChange={(e) => setPatientName(e.target.value)} placeholder="Patient full name" />
        </div>
      )}

      {step === 1 && (
        <div className="grid gap-3 md:grid-cols-2">
          {services.map((s) => (
            <button
              key={s.id}
              type="button"
              onClick={() => setSelectedListing(s)}
              className={`rounded-xl border p-4 text-left ${selectedListing?.id === s.id ? "border-teal-500 bg-teal-50" : "border-slate-200"}`}
            >
              <p className="font-medium">{s.title}</p>
              <p className="text-sm text-slate-500">{formatCurrency(s.base_price)}</p>
            </button>
          ))}
        </div>
      )}

      {step === 2 && (
        <div className="grid gap-3 md:grid-cols-2">
          {partners.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setSelectedPartner(p)}
              className={`rounded-xl border p-4 text-left ${selectedPartner?.id === p.id ? "border-teal-500 bg-teal-50" : "border-slate-200"}`}
            >
              <p className="font-medium">{p.provider_name}</p>
              <p className="text-sm text-slate-500">{p.provider_type}</p>
            </button>
          ))}
        </div>
      )}

      {step === 3 && (
        <div className="space-y-4">
          <Input type="date" value={date} min={todayISO()} onChange={(e) => setDate(e.target.value)} />
          <div className="grid grid-cols-4 gap-2">
            {slots.map((s) => (
              <button
                key={s.id}
                type="button"
                disabled={!s.available}
                onClick={() => setSlot(s)}
                className={`rounded border px-2 py-2 text-sm ${slot?.id === s.id ? "border-teal-600 bg-teal-600 text-white" : ""}`}
              >
                {s.time}
              </button>
            ))}
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="grid gap-3 md:grid-cols-3">
          {(["LAB", "CLINIC", "HOME"] as const).map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setCollectionType(type)}
              className={`flex items-center gap-2 rounded-xl border p-4 ${collectionType === type ? "border-teal-500 bg-teal-50" : ""}`}
            >
              {type === "HOME" ? <Home className="h-5 w-5" /> : type === "CLINIC" ? <Stethoscope className="h-5 w-5" /> : <MapPin className="h-5 w-5" />}
              {type === "HOME" ? "Home" : type === "CLINIC" ? "Clinic" : "Lab"}
            </button>
          ))}
          {collectionType === "HOME" && (
            <div className="md:col-span-3 space-y-2">
              <Input placeholder="Address" value={homeAddress} onChange={(e) => setHomeAddress(e.target.value)} />
              <Input placeholder="Building / apartment" value={building} onChange={(e) => setBuilding(e.target.value)} />
              <Input placeholder="Collector notes" value={collectorNotes} onChange={(e) => setCollectorNotes(e.target.value)} />
            </div>
          )}
        </div>
      )}

      {step === 5 && (
        <Card className="space-y-2 p-4 text-sm">
          <p>Patient: {patientName}</p>
          <p>Service: {selectedListing?.title}</p>
          <p>Provider: {selectedPartner?.provider_name}</p>
          <p>Schedule: {date} {slot?.time}</p>
          <p>Collection: {collectionType}</p>
          <p className="font-semibold">Total: {quotation ? formatCurrency(quotation.total_amount) : "—"}</p>
        </Card>
      )}

      {step === 6 && paymentQr === null && (
        <SectionHeader title="Payment" description="Scan QR to complete payment. Booking is not confirmed until payment succeeds." />
      )}

      {step === 7 && (
        <div className="space-y-4">
          <SectionHeader title="Booking confirmed" description={`Reference ${bookingRef}`} />
          {paymentQr ? <QrPanel payload={paymentQr} caption={bookingRef ?? ""} /> : null}
        </div>
      )}

      {step < 7 && (
        <div className="flex justify-between border-t pt-4">
          <Button variant="ghost" disabled={step === 0} onClick={() => setStep((s) => s - 1)}>
            <ChevronLeft className="h-4 w-4" /> Back
          </Button>
          {step < 5 ? (
            <Button disabled={!canProceed} onClick={() => setStep((s) => s + 1)}>
              Continue <ChevronRight className="h-4 w-4" />
            </Button>
          ) : step === 5 ? (
            <Button disabled={!canProceed} onClick={() => setStep(6)}>
              Proceed to payment
            </Button>
          ) : (
            <Button disabled={busy} onClick={createBookingAndPay}>
              {busy ? "Processing…" : "Pay & confirm"}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
