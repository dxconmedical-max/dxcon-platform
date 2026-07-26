/**
 * Payment domain — types only (re-export). No collection logic here.
 */
export type {
  ReceptionPaymentSummary,
  ReceptionPaymentRecord,
  ReceptionPaymentResult,
  ReceptionOrderDetail,
} from "@/lib/api/reception";

export { RECEPTION_PAYMENT_METHODS, RECEPTION_PAYMENT_TIMEOUT_MS } from "@/lib/api/reception";
