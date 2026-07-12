"use client";

import { useEffect, useState } from "react";

import type { DataSource, Sourced } from "@/lib/api/adapter";
import { normalizeApiError } from "@/lib/errors";

export type SourcedState<T> = {
  data: T | null;
  source: DataSource | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

/**
 * Loads a Sourced<T> payload and tracks loading/error/provenance. State is only
 * mutated inside async resolution (effect) or the reload event handler, keeping
 * it compliant with the react-hooks set-state-in-effect rule.
 *
 * Callers pass an explicit dependency list; the loader identity is intentionally
 * excluded from the effect deps.
 */
export function useSourcedData<T>(
  loader: () => Promise<Sourced<T>>,
  deps: unknown[],
): SourcedState<T> {
  const [state, setState] = useState<{
    data: T | null;
    source: DataSource | null;
    loading: boolean;
    error: string | null;
  }>({ data: null, source: null, loading: true, error: null });
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let cancelled = false;
    loader()
      .then((result) => {
        if (cancelled) return;
        setState({ data: result.value, source: result.source, loading: false, error: null });
      })
      .catch((error) => {
        if (cancelled) return;
        setState({ data: null, source: null, loading: false, error: normalizeApiError(error) });
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce]);

  return {
    ...state,
    reload: () => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      setNonce((n) => n + 1);
    },
  };
}
