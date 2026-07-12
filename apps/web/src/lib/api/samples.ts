/**
 * Labeled sample datasets for Sprint 2 mock adapters.
 *
 * These are ONLY used as fallbacks when a backend capability is not yet
 * implemented or requires entity context the pilot session cannot resolve.
 * Every screen that renders sample data surfaces a "Sample data" badge so the
 * distinction from live production data stays explicit and honest.
 */

import type { CatalogItem, ServiceLocation, TimeSlot } from "./booking";
import type { PatientInvoice, PatientProfile, HealthSummary, PatientBooking } from "./patient-portal";
import type { QueueEntry } from "./reception";
import type { CollectionJob, RouteStop, TimelineEvent } from "./collector";
import type { LabSample, QcItem, VerificationItem } from "./lab";
import type { DoctorReport, DoctorReviewRow } from "./doctor";

export const SAMPLE_CATALOG: CatalogItem[] = [
  { code: "CBC", name: "Complete Blood Count", category: "Hematology", sample_type: "Blood", price: 180000, turnaround_hours: 24, home_collection: true },
  { code: "LIPID", name: "Lipid Panel", category: "Chemistry", sample_type: "Blood", price: 260000, turnaround_hours: 24, home_collection: true },
  { code: "HBA1C", name: "HbA1c (Diabetes)", category: "Chemistry", sample_type: "Blood", price: 220000, turnaround_hours: 24, home_collection: true },
  { code: "TSH", name: "Thyroid Stimulating Hormone", category: "Endocrinology", sample_type: "Blood", price: 240000, turnaround_hours: 48, home_collection: true },
  { code: "VITD", name: "Vitamin D (25-OH)", category: "Chemistry", sample_type: "Blood", price: 420000, turnaround_hours: 48, home_collection: true },
  { code: "PKG-WELL", name: "Wellness Screening Package", category: "Package", sample_type: "Blood + Urine", price: 1290000, turnaround_hours: 48, home_collection: true },
];

export const SAMPLE_LOCATIONS: ServiceLocation[] = [
  { id: "loc-hcm-d1", name: "DxCon Central Lab — District 1", city: "Ho Chi Minh City", address: "12 Nguyen Hue, District 1", home_collection: true },
  { id: "loc-hcm-d7", name: "DxCon Collection Point — District 7", city: "Ho Chi Minh City", address: "88 Nguyen Thi Thap, District 7", home_collection: true },
  { id: "loc-hn-bd", name: "DxCon Hanoi Lab — Ba Dinh", city: "Hanoi", address: "5 Doi Can, Ba Dinh", home_collection: true },
];

export function sampleSlots(dateISO: string): TimeSlot[] {
  const times = ["07:30", "08:30", "09:30", "10:30", "13:30", "14:30", "15:30", "16:30"];
  return times.map((time, index) => ({
    id: `${dateISO}-${time}`,
    date: dateISO,
    time,
    capacity: 4,
    booked: index % 3,
    available: index % 3 < 4,
  }));
}

export const SAMPLE_PATIENT_BOOKINGS: PatientBooking[] = [
  { reference: "BKG-24815", service: "Wellness Screening Package", scheduled_at: "2026-07-14 08:30", location: "Home collection — District 7", status: "CONFIRMED" },
  { reference: "BKG-24788", service: "Lipid Panel", scheduled_at: "2026-07-02 09:30", location: "DxCon Central Lab — District 1", status: "COMPLETED" },
  { reference: "BKG-24610", service: "HbA1c", scheduled_at: "2026-06-18 07:30", location: "Home collection — District 1", status: "COMPLETED" },
];

export const SAMPLE_INVOICES: PatientInvoice[] = [
  { invoice_no: "INV-90231", issued_at: "2026-07-02", amount: 260000, currency: "VND", status: "PAID", description: "Lipid Panel" },
  { invoice_no: "INV-90455", issued_at: "2026-07-12", amount: 1290000, currency: "VND", status: "DUE", description: "Wellness Screening Package" },
];

export const SAMPLE_PROFILE: PatientProfile = {
  full_name: "Nguyen Van A",
  patient_code: "PT-100245",
  date_of_birth: "1988-05-12",
  gender: "Male",
  phone: "+84 90 123 4567",
  email: "patient@example.com",
  address: "88 Nguyen Thi Thap, District 7, Ho Chi Minh City",
  blood_type: "O+",
};

export const SAMPLE_HEALTH_SUMMARY: HealthSummary = {
  generated_at: "2026-07-12",
  headline: "Most recent results are within normal ranges, with one value to monitor.",
  highlights: [
    "Lipid panel: LDL cholesterol slightly elevated (3.6 mmol/L) — consider dietary review.",
    "HbA1c: 5.4% — normal, no indication of diabetes.",
    "Complete blood count: all values within reference ranges.",
  ],
  recommendation:
    "Discuss LDL cholesterol with your doctor. Re-test lipid panel in 3 months. This AI-generated summary requires clinician review and is not a diagnosis.",
};

export const SAMPLE_QUEUE: QueueEntry[] = [
  { id: "Q-01", patient_name: "Tran Thi B", patient_code: "PT-100311", service: "Walk-in — CBC", checked_in: false, arrived_at: "08:05", status: "WAITING" },
  { id: "Q-02", patient_name: "Le Van C", patient_code: "PT-100298", service: "Booking BKG-24815", checked_in: true, arrived_at: "08:12", status: "CHECKED_IN" },
  { id: "Q-03", patient_name: "Pham Thi D", patient_code: "PT-100322", service: "Home collection follow-up", checked_in: false, arrived_at: "08:20", status: "WAITING" },
];

export const SAMPLE_COLLECTION_JOBS: CollectionJob[] = [
  { assignment_id: "JOB-5521", patient_name: "Hoang Van E", address: "12 Le Loi, District 1", scheduled_at: "08:30", service: "CBC + Lipid", status: "ASSIGNED", priority: "NORMAL" },
  { assignment_id: "JOB-5522", patient_name: "Vo Thi F", address: "45 Vo Van Tan, District 3", scheduled_at: "09:15", service: "HbA1c", status: "EN_ROUTE", priority: "URGENT" },
  { assignment_id: "JOB-5523", patient_name: "Dang Van G", address: "88 Nguyen Thi Thap, District 7", scheduled_at: "10:00", service: "Wellness Package", status: "COMPLETED", priority: "NORMAL" },
];

export const SAMPLE_ROUTE_STOPS: RouteStop[] = [
  { sequence: 1, label: "Hoang Van E — 12 Le Loi, District 1", eta: "08:30", status: "PENDING" },
  { sequence: 2, label: "Vo Thi F — 45 Vo Van Tan, District 3", eta: "09:15", status: "PENDING" },
  { sequence: 3, label: "Dang Van G — 88 Nguyen Thi Thap, District 7", eta: "10:00", status: "DONE" },
];

export const SAMPLE_TIMELINE: TimelineEvent[] = [
  { at: "10:02", event: "Sample handed over to lab courier", actor: "Collector 12", location: "District 7" },
  { at: "09:58", event: "Specimen photo uploaded", actor: "Collector 12", location: "District 7" },
  { at: "09:45", event: "Collection completed — JOB-5523", actor: "Collector 12", location: "District 7" },
  { at: "08:35", event: "Route started", actor: "Collector 12", location: "District 1" },
];

export const SAMPLE_LAB_SAMPLES: LabSample[] = [
  { sample_code: "SMP-77120", order_code: "ORD-4410", test: "CBC", received_at: "08:40", condition: "OK", status: "RECEIVED" },
  { sample_code: "SMP-77121", order_code: "ORD-4411", test: "Lipid Panel", received_at: "08:52", condition: "OK", status: "IN_TESTING" },
  { sample_code: "SMP-77122", order_code: "ORD-4412", test: "HbA1c", received_at: "09:05", condition: "Hemolyzed", status: "RECEIVED" },
];

export const SAMPLE_QC: QcItem[] = [
  { sample_code: "SMP-77121", test: "Lipid Panel", control_lot: "LOT-2291", status: "PENDING", note: "Awaiting Level 2 control" },
  { sample_code: "SMP-77118", test: "CBC", control_lot: "LOT-2290", status: "PASS", note: "Within 2SD" },
];

export const SAMPLE_VERIFICATION: VerificationItem[] = [
  { order_code: "ORD-4411", test: "Lipid Panel", result_value: "LDL 3.6 mmol/L", abnormal: true, status: "AWAITING_VERIFICATION" },
  { order_code: "ORD-4410", test: "CBC", result_value: "All within range", abnormal: false, status: "AWAITING_VERIFICATION" },
  { order_code: "ORD-4408", test: "HbA1c", result_value: "5.4%", abnormal: false, status: "VERIFIED" },
];

export const SAMPLE_DOCTOR_REVIEWS: DoctorReviewRow[] = [
  { report_code: "RPT-33021", patient_name: "Nguyen Van A", patient_code: "PT-100245", status: "AWAITING_REVIEW", collected_at: "2026-07-11 08:30" },
  { report_code: "RPT-33019", patient_name: "Tran Thi B", patient_code: "PT-100311", status: "AWAITING_REVIEW", collected_at: "2026-07-11 07:50" },
  { report_code: "RPT-32990", patient_name: "Le Van C", patient_code: "PT-100298", status: "SIGNED", collected_at: "2026-07-10 15:10" },
];

export const SAMPLE_DOCTOR_REPORT: DoctorReport = {
  report_code: "RPT-33021",
  patient_name: "Nguyen Van A",
  patient_code: "PT-100245",
  collected_at: "2026-07-11 08:30",
  status: "AWAITING_REVIEW",
  analytes: [
    { name: "LDL Cholesterol", value: "3.6", unit: "mmol/L", reference: "< 3.4", abnormal: true, flag: "HIGH" },
    { name: "HDL Cholesterol", value: "1.3", unit: "mmol/L", reference: "> 1.0", abnormal: false },
    { name: "Triglycerides", value: "1.4", unit: "mmol/L", reference: "< 1.7", abnormal: false },
    { name: "Total Cholesterol", value: "5.4", unit: "mmol/L", reference: "< 5.2", abnormal: true, flag: "HIGH" },
  ],
  ai_interpretation:
    "Pattern consistent with mild hyperlipidemia (elevated LDL and total cholesterol). Suggest lifestyle counseling and 3-month re-test. AI-assisted draft — requires clinician confirmation.",
};
