/**
 * Receipt service facade — thin client over reception workspace receipt APIs.
 * Does not duplicate payment collection.
 */
export {
  fetchReceptionReceipt,
  previewReceptionReceipt,
  printReceptionReceipt,
  reprintReceptionReceipt,
  cancelReceptionReceipt,
  fetchOrderReceipts,
  receptionReceiptPdfUrl,
} from "@/lib/api/reception";
