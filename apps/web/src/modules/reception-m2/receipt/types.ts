/** Receipt domain types — maps BizReceipt + preview payloads. */
export type {
  ReceptionPaymentRecord,
  ReceptionPaymentResult,
} from "@/lib/api/reception";

export type ReceptionReceipt = {
  id?: string;
  receipt_code: string;
  payment_id: string;
  order_id: string;
  invoice_id?: string | null;
  status: string;
  print_count: number;
  preferred_format?: string;
  pdf_available?: boolean;
  issued_at?: string | null;
  issued_by?: string | null;
  last_printed_at?: string | null;
  last_printed_by?: string | null;
  cancelled_at?: string | null;
  cancelled_by?: string | null;
  cancel_reason?: string | null;
  html_snapshot?: string | null;
  thermal_payload?: string | null;
};

export type ReceptionReceiptPreview = {
  html: string;
  thermal_text?: string;
  thermal_html?: string;
  context?: Record<string, unknown>;
};
