export function useReceptionLabQueueArchitecture() {
  return {
    status: "engine_ready" as const,
    message:
      "Lab Queue supports enqueue, priority, waiting→verified workflow, statistics, and live refresh.",
    stages: ["waiting", "processing", "completed", "verified"] as const,
    pipeline: [
      "paid",
      "barcode",
      "lab_queue",
      "waiting",
      "processing",
      "completed",
      "verified",
    ] as const,
  };
}
