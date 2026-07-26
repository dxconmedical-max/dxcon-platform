/**
 * Payment service facade — re-exports Release 1 reception client.
 * Do not duplicate mappers or HTTP here.
 */
export {
  collectReceptionPayment,
  fetchReceptionOrder,
  fetchReceptionPaymentHistory,
  getOrderCode,
} from "@/lib/api/reception";
