"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import {
  advanceSampleQueueOrder,
  enqueueSampleQueueOrder,
  fetchSampleQueueDashboard,
  fetchSampleQueueHistory,
  refreshSampleQueue,
  trackSampleQueueOrder,
  updateSampleQueueTracking,
  type SampleQueueDashboard,
  type SampleQueueEvent,
  type SampleQueueItem,
} from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

const NEXT_STAGE: Record<string, string | null> = {
  collected: "transport",
  transport: "received",
  received: "sorting",
  sorting: "laboratory",
  laboratory: "completed",
  completed: null,
};

const REFRESH_MS = 5000;

export function SampleQueueWorkbench() {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = useMemo(
    () => ({ token: accessToken || "", organizationId: activeOrganizationId }),
    [accessToken, activeOrganizationId],
  );

  const [dash, setDash] = useState<SampleQueueDashboard | null>(null);
  const [stageFilter, setStageFilter] = useState("");
  const [enqueueRef, setEnqueueRef] = useState("");
  const [trackRef, setTrackRef] = useState("");
  const [history, setHistory] = useState<SampleQueueEvent[]>([]);
  const [tracked, setTracked] = useState<SampleQueueItem | null>(null);
  const [locationNote, setLocationNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [live, setLive] = useState(true);
  const versionRef = useRef(0);

  const applyDashboard = useCallback((data: SampleQueueDashboard) => {
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
      const data = await fetchSampleQueueDashboard(ctx, {
        stage: stageFilter || undefined,
      });
      applyDashboard(data);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }, [ctx, stageFilter, applyDashboard]);

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
          const data = await refreshSampleQueue(ctx, { version: versionRef.current });
          applyDashboard(data);
        } catch {
          /* keep last board */
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
      await enqueueSampleQueueOrder(ctx, enqueueRef.trim(), {
        location: locationNote || undefined,
      });
      setMessage(`Sample queue entered for ${enqueueRef.trim()}`);
      setEnqueueRef("");
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onAdvance(item: SampleQueueItem) {
    const next = NEXT_STAGE[item.stage];
    if (!next || !ctx.token) return;
    setBusy(true);
    setError(null);
    try {
      await advanceSampleQueueOrder(ctx, item.order_code, next, {
        location: locationNote || undefined,
      });
      await load();
      if (trackRef === item.order_code) {
        const h = await fetchSampleQueueHistory(ctx, item.order_code);
        setHistory(h);
      }
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onTrack() {
    if (!ctx.token || !trackRef.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const snap = await trackSampleQueueOrder(ctx, trackRef.trim());
      setTracked(snap);
      const h = await fetchSampleQueueHistory(ctx, trackRef.trim());
      setHistory(h);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onUpdateLocation(orderCode: string) {
    if (!ctx.token || !locationNote.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await updateSampleQueueTracking(ctx, orderCode, { location: locationNote.trim() });
      setMessage(`Location updated for ${orderCode}`);
      await load();
      await onTrack();
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
            <option value="collected">Collected</option>
            <option value="transport">Transport</option>
            <option value="received">Received</option>
            <option value="sorting">Sorting</option>
            <option value="laboratory">Laboratory</option>
            <option value="completed">Completed</option>
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
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6 text-sm">
          {[
            ["Collected", stats.by_stage.collected ?? 0],
            ["Transport", stats.by_stage.transport ?? 0],
            ["Received", stats.by_stage.received ?? 0],
            ["Sorting", stats.by_stage.sorting ?? 0],
            ["Laboratory", stats.by_stage.laboratory ?? 0],
            ["Completed", stats.completed],
          ].map(([label, value]) => (
            <div key={String(label)} className="rounded border px-3 py-2">
              <p className="text-xs text-neutral-500">{label}</p>
              <p className="text-lg font-semibold">{value}</p>
            </div>
          ))}
        </div>
      ) : null}

      <p className="text-xs text-neutral-600">
        Workflow: collected → transport → received → sorting → laboratory → completed
      </p>

      <div className="flex flex-wrap gap-2">
        <Input
          value={enqueueRef}
          onChange={(e) => setEnqueueRef(e.target.value)}
          placeholder="ORD-… enqueue (collect if needed)"
          className="max-w-xs"
        />
        <Input
          value={locationNote}
          onChange={(e) => setLocationNote(e.target.value)}
          placeholder="Location / note"
          className="max-w-xs"
        />
        <Button type="button" disabled={busy || !enqueueRef.trim()} onClick={() => void onEnqueue()}>
          Enter sample queue
        </Button>
      </div>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}

      <div className="overflow-x-auto rounded border">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-neutral-50 text-xs uppercase text-neutral-500">
            <tr>
              <th className="px-3 py-2">Order</th>
              <th className="px-3 py-2">Sample</th>
              <th className="px-3 py-2">Patient</th>
              <th className="px-3 py-2">Stage</th>
              <th className="px-3 py-2">Location</th>
              <th className="px-3 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {(dash?.items ?? []).map((item) => (
              <tr key={item.id || item.order_code} className="border-t">
                <td className="px-3 py-2 font-mono text-xs">{item.order_code}</td>
                <td className="px-3 py-2 font-mono text-xs">{item.sample_code || "—"}</td>
                <td className="px-3 py-2">
                  {item.patient_name}
                  <div className="text-xs text-neutral-500">{item.patient_code}</div>
                </td>
                <td className="px-3 py-2 capitalize">{item.stage}</td>
                <td className="px-3 py-2 text-xs">{item.location || "—"}</td>
                <td className="px-3 py-2">
                  <div className="flex flex-wrap gap-1">
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
                      <span className="text-xs text-emerald-700">Completed</span>
                    )}
                    <Button
                      type="button"
                      variant="ghost"
                      disabled={busy}
                      onClick={() => {
                        setTrackRef(item.order_code);
                        void (async () => {
                          setTrackRef(item.order_code);
                          const snap = await trackSampleQueueOrder(ctx, item.order_code);
                          setTracked(snap);
                          setHistory(await fetchSampleQueueHistory(ctx, item.order_code));
                        })();
                      }}
                    >
                      History
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
            {!dash?.items?.length ? (
              <tr>
                <td colSpan={6} className="px-3 py-6 text-center text-neutral-500">
                  No sample queue items. Enqueue a collected specimen order.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>

      <div className="space-y-2 rounded border border-dashed p-3">
        <p className="text-sm font-medium">Realtime tracking & history</p>
        <div className="flex flex-wrap gap-2">
          <Input
            value={trackRef}
            onChange={(e) => setTrackRef(e.target.value)}
            placeholder="ORD-… track"
            className="max-w-xs"
          />
          <Button type="button" disabled={busy || !trackRef.trim()} onClick={() => void onTrack()}>
            Track
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={busy || !trackRef.trim() || !locationNote.trim()}
            onClick={() => void onUpdateLocation(trackRef.trim())}
          >
            Update location
          </Button>
        </div>
        {tracked ? (
          <p className="text-sm">
            {tracked.order_code} · <span className="capitalize">{tracked.stage || "off queue"}</span>
            {tracked.location ? ` · ${tracked.location}` : ""}
          </p>
        ) : null}
        {history.length ? (
          <ul className="max-h-48 space-y-1 overflow-auto text-xs font-mono">
            {history.map((ev) => (
              <li key={ev.id}>
                {ev.created_at} · {ev.event_type} · {ev.from_stage || "—"} → {ev.to_stage || "—"}
                {ev.location ? ` · ${ev.location}` : ""}
                {ev.actor ? ` · ${ev.actor}` : ""}
                {ev.note ? ` · ${ev.note}` : ""}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </div>
  );
}
