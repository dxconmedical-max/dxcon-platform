"use client";

import { useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import {
  createAddon,
  findAddonCandidates,
  listAddonTests,
  type AddonCandidate,
  type AddonTest,
} from "@/lib/api/addons";

export default function AddonsPage() {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = accessToken ? { token: accessToken, organizationId: activeOrganizationId } : null;
  const [q, setQ] = useState("");
  const [orders, setOrders] = useState<AddonCandidate[]>([]);
  const [picked, setPicked] = useState<AddonCandidate | null>(null);
  const [tq, setTq] = useState("");
  const [tests, setTests] = useState<AddonTest[]>([]);
  const [chosen, setChosen] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  async function run<T>(fn: () => Promise<T>): Promise<T | null> {
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (err) {
      setError(normalizeApiError(err));
      return null;
    } finally {
      setBusy(false);
    }
  }

  async function searchOrders() {
    if (!ctx) return;
    setDone(null);
    const r = await run(() => findAddonCandidates(ctx, q.trim()));
    if (r) setOrders(r);
  }

  async function searchTests(order: AddonCandidate, term: string) {
    if (!ctx) return;
    const r = await run(() => listAddonTests(ctx, order.order_code, term.trim()));
    if (r) setTests(r);
  }

  async function pick(order: AddonCandidate) {
    setPicked(order);
    setChosen(new Set());
    setTq("");
    setDone(null);
    await searchTests(order, "");
  }

  function toggle(id: string) {
    setChosen((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function submit() {
    if (!ctx || !picked || chosen.size === 0) return;
    const r = await run(() => createAddon(ctx, picked.order_code, Array.from(chosen)));
    if (r) {
      setDone(r.addon_order_code);
      setPicked(null);
      setTests([]);
      setChosen(new Set());
    }
  }

  return (
    <AppShell title="Làm thêm xét nghiệm" workspacePath="/app/reception">
      <div className="space-y-4">
        <div>
          <h1 className="text-xl font-semibold">Làm thêm xét nghiệm trên mẫu đã thu</h1>
          <p className="text-sm text-slate-600">
            Tìm đơn đã thu mẫu (mã đơn, tên hoặc mã bệnh nhân), chọn xét nghiệm cần làm thêm. Mặc định trong 72 giờ kể từ lúc thu mẫu, mỗi xét nghiệm có thể đặt thời hạn riêng.
          </p>
        </div>
        <div className="flex gap-2">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void searchOrders()}
            placeholder="Mã đơn / tên bệnh nhân"
            aria-label="Tìm đơn"
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <Button disabled={busy || q.trim().length < 2} onClick={() => void searchOrders()}>
            Tìm đơn
          </Button>
        </div>
        {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
        {done ? <p className="rounded-lg bg-green-50 p-3 text-sm text-green-800">Đã tạo đơn làm thêm {done}.</p> : null}

        {!picked ? (
          <ul className="space-y-2">
            {orders.map((o) => (
              <li key={o.order_code} className="rounded-xl border border-slate-200 bg-white p-3">
                <p className="font-medium">{o.patient_name} · {o.order_code}</p>
                <p className="text-sm text-slate-600">{o.tests.join(", ")}</p>
                <p className="text-xs text-slate-400">Thu mẫu cách đây {o.hours_since_collected} giờ</p>
                <Button size="sm" className="mt-2" onClick={() => void pick(o)}>Chọn đơn này</Button>
              </li>
            ))}
          </ul>
        ) : (
          <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4">
            <p className="font-medium">
              Đơn {picked.order_code} · {picked.patient_name}
            </p>
            <div className="flex gap-2">
              <input
                value={tq}
                onChange={(e) => setTq(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && void searchTests(picked, tq)}
                placeholder="Tìm xét nghiệm"
                aria-label="Tìm xét nghiệm"
                className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <Button variant="outline" disabled={busy} onClick={() => void searchTests(picked, tq)}>Tìm</Button>
            </div>
            <ul className="space-y-1">
              {tests.map((t) => (
                <li key={t.id}>
                  <label className={`flex items-start gap-2 text-sm ${t.allowed ? "" : "opacity-50"}`}>
                    <input type="checkbox" disabled={!t.allowed} checked={chosen.has(t.id)} onChange={() => toggle(t.id)} />
                    <span>
                      {t.name} ({t.code})
                      {t.already_in_order ? " — đã có trong đơn" : t.allowed ? ` — còn ${t.hours_left} giờ` : ` — quá ${t.window_hours} giờ`}
                      {t.is_sendout ? " — gửi ngoài" : ""}
                    </span>
                  </label>
                </li>
              ))}
            </ul>
            <div className="flex gap-2">
              <Button disabled={busy || chosen.size === 0} onClick={() => void submit()}>
                {busy ? "Đang tạo…" : `Tạo đơn làm thêm (${chosen.size})`}
              </Button>
              <Button variant="outline" onClick={() => setPicked(null)}>Chọn đơn khác</Button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
