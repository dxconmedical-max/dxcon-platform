/**
 * Payment hooks — architecture stub wrapping engine-backed APIs.
 * Collect UI remains in workflow OrderSteps until dedicated M2 page kickoff.
 */
export function useReceptionPaymentArchitecture() {
  return {
    status: "engine_ready" as const,
    message:
      "Payment Engine supports cash/transfer/partial/history via @/lib/api/reception. Dedicated M2 Payment page UI not required for Step 3.",
    partial_payments_supported: true,
    methods: ["cash", "transfer", "qr", "pos", "corporate", "insurance"] as const,
  };
}
