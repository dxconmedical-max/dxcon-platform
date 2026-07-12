import { ApiError } from "@/lib/errors";

/**
 * Data provenance for Sprint 2 screens.
 * - "live"   : returned by the production backend
 * - "sample" : produced by a labeled mock adapter because the backend
 *              capability is not implemented yet or requires context we
 *              cannot resolve for the current pilot session.
 */
export type DataSource = "live" | "sample";

export type Sourced<T> = {
  value: T;
  source: DataSource;
  note?: string;
};

/**
 * Run a live backend call and fall back to a labeled sample payload when the
 * capability is unavailable (missing endpoint, missing entity context, or a
 * server error the pilot cannot recover from). Auth/permission failures are
 * re-thrown so the shell can route to /login or /forbidden.
 */
export async function withSampleFallback<T>(
  live: () => Promise<T>,
  sample: T,
  note?: string,
): Promise<Sourced<T>> {
  try {
    const value = await live();
    return { value, source: "live" };
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      throw error;
    }
    return { value: sample, source: "sample", note };
  }
}

export const SAMPLE_NOTE =
  "Sample data shown — connect this capability to the production API to see live records.";
