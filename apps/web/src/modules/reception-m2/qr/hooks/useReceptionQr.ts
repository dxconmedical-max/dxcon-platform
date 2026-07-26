export function useReceptionQrArchitecture() {
  return {
    status: "engine_ready" as const,
    message:
      "QR Engine supports payment, VNPay, static, dynamic, sample, and tracking codes with verification.",
    kinds: ["payment", "vnpay", "static", "dynamic", "sample", "tracking"] as const,
  };
}
