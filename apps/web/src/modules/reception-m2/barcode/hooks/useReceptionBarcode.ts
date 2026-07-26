export function useReceptionBarcodeArchitecture() {
  return {
    status: "engine_ready" as const,
    message:
      "Barcode Engine supports order/sample/collection labels, thermal sheets, and printer adapters.",
    labelTypes: ["order", "sample", "collection", "patient"] as const,
    printers: ["browser", "thermal"] as const,
  };
}
