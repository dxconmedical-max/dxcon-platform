"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import {
  advanceLabQueueOrder,
  enqueueLabQueueOrder,
  fetchLabQueueDashboard,
  refreshLabQueue,
  setLabQueuePriority,
  type LabQueueDashboard,
  type LabQueueItem,
} from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

const NEXT_STAGE: Record<string, string | null> = {
  waiting: "processing",
  processing: "completed",
  completed: "verified",
  verified: null,
};

const REFRESH_MS = 5000;

export function LabQueueWorkbench() {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = useMemo(
    () => ({ token: accessToken || "", organizationId: activeOrganizationId }),
    [accessToken, activeOrganizationId],
  );

  const [dash, setDash] = useState<LabQueueDashboard | null>(null);
  const [stageFilter, setStageFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [enqueueRef, setEnqueueRef] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [live, setLive] = useState(true);
  const versionRef = useRef(0);

  const applyDashboard = useCallback((data: LabQueueDashboard) => {
    versionRef.current = data.version;
    setDash((prev) => {
      if (!data.changed && prev && data.items.length === 0) {
        return {
          ...prev,
          refreshed_at: data.refreshed_at,
          version: data.version,
          changed: false,
          statistics: data.statistics,
        };
      }
      return data;
    });
  }, []);

  const load = useCallback(async () => {
    if (!ctx.token) return;
    setBusy(true);
    setError(null);
    try {
      const data = await fetchLabQueueDashboard(ctx, {
        stage: stageFilter || undefined,
        priority: priorityFilter || undefined,
      });
      applyDashboard(data);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }, [ctx, stageFilter, priorityFilter, applyDashboard]);

  useEffect(() => {
    const t = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(t);
  }, [load]);

  useEffect(() => {
    if (!live || !ctx.token) return;
    const id = window.setInterval(() => {
      void (async () => {
        try {
          const data = await refreshLabQueue(ctx, { version: versionRef.current });
          applyDashboard(data);
        } catch {
          /* keep last good board on poll errors */
        }
      })();
    }, REFRESH_MS);
    return () => window.clearInterval(id);
  }, [live, ctx, applyDashboard]);

  async function onEnqueue() {
    if (!ctx.token || !enqueueRef.trim()) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await enqueueLabQueueOrder(ctx, enqueueRef.trim(), {
        priority: priorityFilter || "routine",
      });
      setMessage(`Enqueued ${enqueueRef.trim()}`);
      setEnqueueRef("");
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onAdvance(item: LabQueueItem) {
    const next = NEXT_STAGE[item.stage];
    if (!next || !ctx.token) return;
    setBusy(true);
    setError(null);
    try {
      await advanceLabQueueOrder(ctx, item.order_code, next);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onPriority(item: LabQueueItem, priority: string) {
    if (!ctx.token) return;
    setBusy(true);
    setError(null);
    try {
      await setLabQueuePriority(ctx, item.order_code, priority);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  const stats = dash?.statistics;

  return (
    <div className="mx-auto max-w-6xl space-y-4 py-4">
      <div className="flex flex-wrap items-end gap-2 text-sm">
        <label>
          Stage{" "}
          <select
            className="rounded border px-2 py-1"
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
          >
            <option value="">All</option>
            <option value="waiting">Waiting</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="verified">Verified</option>
          </select>
        </label>
        <label>
          Priority{" "}
          <select
            className="rounded border px-2 py-1"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
          >
            <option value="">All</option>
            <option value="urgent">Urgent</option>
            <option value="high">High</option>
            <option value="routine">Routine</option>
            <option value="low">Low</option>
          </select>
        </label>
        <Button type="button" disabled={busy} onClick={() => void load()}>
          Refresh
        </Button>
        <label className="inline-flex items-center gap-2">
          <input type="checkbox" checked={live} onChange={(e) => setLive(e.target.checked)} />
          Live ({REFRESH_MS / 1000}s)
        </label>
        {dash?.refreshed_at ? (
          <span className="text-xs text-neutral-500">
            v{dash.version} · {new Date(dash.refreshed_at).toLocaleTimeString()}
          </span>
        ) : null}
      </div>

      {stats ? (
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-7 text-sm">
          {[
            ["Waiting", stats.waiting],
            ["Processing", stats.processing],
            ["Completed", stats.completed],
            ["Verified", stats.verified],
            ["Active", stats.active],
            ["Paid not queued", stats.paid_not_queued],
            ["Barcode ready", stats.barcode_ready_not_queued],
          ].map(([label, value]) => (
            <div key={String(label)} className="rounded border px-3 py-2">
              <p className="text-xs text-neutral-500">{label}</p>
              <p className="text-lg font-semibold">{value}</p>
            </div>
          ))}
        </div>
      ) : null}

      <p className="text-xs text-neutral-600">
        Pipeline: paid → barcode → lab queue → waiting → processing → completed → verified
      </p>

      <div className="flex flex-wrap gap-2">
        <Input
          value={enqueueRef}
          onChange={(e) => setEnqueueRef(e.target.value)}
          placeholder="ORD-… to enqueue (handoff)"
          className="max-w-xs"
        />
        <Button type="button" disabled={busy || !enqueueRef.trim()} onClick={() => void onEnqueue()}>
          Enqueue to lab
        </Button>
      </div>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}

      <div className="overflow-x-auto rounded border">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-neutral-50 text-xs uppercase text-neutral-500">
            <tr>
              <th className="px-3 py-2">Priority</th>
              <th className="px-3 py-2">Order</th>
              <th className="px-3 py-2">Patient</th>
              <th className="px-3 py-2">Stage</th>
              <th className="px-3 py-2">Tests</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {(dash?.items ?? []).map((item) => (
              <tr key={item.id || item.order_code} className="border-t">
                <td className="px-3 py-2">
                  <select
                    className="rounded border px-1 py-0.5 text-xs"
                    value={item.priority}
                    disabled={busy || item.stage === "verified"}
                    onChange={(e) => void onPriority(item, e.target.value)}
                  >
                    <option value="urgent">urgent</option>
                    <option value="high">high</option>
                    <option value="routine">routine</option>
                    <option value="low">low</option>
                  </select>
                </td>
                <td className="px-3 py-2 font-mono text-xs">{item.order_code}</td>
                <td className="px-3 py-2">
                  {item.patient_name}
                  <div className="text-xs text-neutral-500">{item.patient_code}</div>
                </td>
                <td className="px-3 py-2 capitalize">{item.stage}</td>
                <td className="px-3 py-2 text-xs">
                  {(item.tests ?? []).map((t) => t.test_code).filter(Boolean).join(", ") || "—"}
                </td>
                <td className="px-3 py-2">
                  {NEXT_STAGE[item.stage] ? (
                    <Button
                      type="button"
                      variant="outline"
                      disabled={busy}
                      onClick={() => void onAdvance(item)}
                    >
                      → {NEXT_STAGE[item.stage]}
                    </Button>
                  ) : (
                    <span className="text-xs text-emerald-700">Verified</span>
                  )}
                </td>
              </tr>
            ))}
            {!dash?.items?.length ? (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-neutral-500">
                  No lab queue items. Enqueue a paid + barcoded order.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </div>
  );
}
