/** Receipt hooks — thin orchestration over receipt APIs. */
export function useReceptionReceiptArchitecture() {
  return {
    status: "engine_ready" as const,
    message:
      "Receipt Engine supports preview, print, thermal, PDF, reprint, cancel via @/lib/api/reception.",
    formats: ["standard", "thermal"] as const,
  };
}
