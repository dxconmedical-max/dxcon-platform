export function useReceptionSampleQueueArchitecture() {
  return {
    status: "engine_ready" as const,
    message:
      "Sample Queue supports collected→completed workflow, realtime tracking, history, and audit.",
    stages: [
      "collected",
      "transport",
      "received",
      "sorting",
      "laboratory",
      "completed",
    ] as const,
  };
}
