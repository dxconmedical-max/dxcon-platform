export {
  fetchSampleQueueDashboard,
  refreshSampleQueue,
  enqueueSampleQueueOrder,
  advanceSampleQueueOrder,
  trackSampleQueueOrder,
  fetchSampleQueueHistory,
  updateSampleQueueTracking,
  fetchReceptionLabHandoff,
  fetchReceptionBarcodes,
} from "@/lib/api/reception";

/** Legacy handoff → sample-queue view mapper (still useful for status panels). */
export function mapHandoffToSampleQueueView(handoff: {
  order_code: string;
  queue_reference: string | null;
  collection: Record<string, unknown> | null;
  queue_entry: Record<string, unknown> | null;
  barcodes?: { sample_count?: number };
}): {
  order_code: string;
  queue_reference: string | null;
  collection: Record<string, unknown> | null;
  queue_entry: Record<string, unknown> | null;
  sample_count?: number;
} {
  return {
    order_code: handoff.order_code,
    queue_reference: handoff.queue_reference,
    collection: handoff.collection,
    queue_entry: handoff.queue_entry,
    sample_count: handoff.barcodes?.sample_count,
  };
}
