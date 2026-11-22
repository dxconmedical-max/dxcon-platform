"use client";

import { useEffect, useRef, useState } from "react";

import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { fetchCollectors, googleMapsUrl, type LiveCollector } from "@/lib/api/liveLocation";
import { normalizeApiError } from "@/lib/errors";
import { useAuthStore } from "@/stores/authStore";

const POLL_MS = 10000;
const LEAFLET_JS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js";
const LEAFLET_CSS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css";

type LatLng = [number, number];
type LMap = {
  setView: (c: LatLng, zoom: number) => LMap;
  fitBounds: (points: LatLng[], opts?: Record<string, unknown>) => void;
  remove: () => void;
};
type LMarker = {
  addTo: (m: LMap) => LMarker;
  setLatLng: (p: LatLng) => void;
  remove: () => void;
  bindTooltip: (text: string) => LMarker;
};
type Leaflet = {
  map: (el: HTMLElement, opts?: Record<string, unknown>) => LMap;
  tileLayer: (url: string, opts: Record<string, unknown>) => { addTo: (m: LMap) => void };
  circleMarker: (p: LatLng, opts: Record<string, unknown>) => LMarker;
};
type WindowWithLeaflet = Window & { L?: Leaflet };

let loader: Promise<Leaflet> | null = null;

function loadLeaflet(): Promise<Leaflet> {
  const w = window as WindowWithLeaflet;
  if (w.L?.map) return Promise.resolve(w.L);
  if (loader) return loader;
  loader = new Promise<Leaflet>((resolve, reject) => {
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = LEAFLET_CSS;
    document.head.appendChild(css);
    const script = document.createElement("script");
    script.src = LEAFLET_JS;
    script.async = true;
    script.onload = () => {
      const lib = (window as WindowWithLeaflet).L;
      if (lib) resolve(lib);
      else reject(new Error("Bản đồ không tải được."));
    };
    script.onerror = () => reject(new Error("Bản đồ không tải được."));
    document.head.appendChild(script);
  });
  loader.catch(() => {
    loader = null;
  });
  return loader;
}

function ageText(iso: string, now: number): string {
  const sec = Math.max(0, Math.round((now - new Date(iso).getTime()) / 1000));
  if (sec < 60) return `${sec} giây trước`;
  return `${Math.round(sec / 60)} phút trước`;
}

export function LiveMap() {
  const token = useAuthStore((s) => s.accessToken);
  const organizationId = useAuthStore((s) => s.activeOrganizationId);
  const [items, setItems] = useState<LiveCollector[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [mapError, setMapError] = useState<string | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const mapEl = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<LMap | null>(null);
  const libRef = useRef<Leaflet | null>(null);
  const markers = useRef<Map<string, LMarker>>(new Map());
  const fitted = useRef(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    async function tick() {
      try {
        const list = await fetchCollectors({ token, organizationId });
        if (cancelled) return;
        setItems(list);
        setError(null);
        setNow(Date.now());
      } catch (err) {
        if (!cancelled) setError(normalizeApiError(err));
      }
    }
    void tick();
    const id = setInterval(() => void tick(), POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [token, organizationId]);

  useEffect(() => {
    if (!mapEl.current) return;
    let cancelled = false;
    loadLeaflet()
      .then((lib) => {
        if (cancelled || !mapEl.current || mapRef.current) return;
        libRef.current = lib;
        const map = lib.map(mapEl.current).setView([10.7769, 106.7009], 11);
        lib
          .tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
            maxZoom: 19,
            attribution: "© OpenStreetMap contributors",
          })
          .addTo(map);
        mapRef.current = map;
      })
      .catch((err: unknown) => setMapError(err instanceof Error ? err.message : "Lỗi bản đồ."));
    return () => {
      cancelled = true;
      mapRef.current?.remove();
      mapRef.current = null;
      markers.current.clear();
      fitted.current = false;
    };
  }, []);

  useEffect(() => {
    const lib = libRef.current;
    const map = mapRef.current;
    if (!lib || !map) return;
    const seen = new Set<string>();
    const points: LatLng[] = [];
    for (const c of items) {
      const pos: LatLng = [c.latitude, c.longitude];
      seen.add(c.user_id);
      points.push(pos);
      const existing = markers.current.get(c.user_id);
      if (existing) existing.setLatLng(pos);
      else {
        markers.current.set(
          c.user_id,
          lib
            .circleMarker(pos, { radius: 9, color: "#0f766e", weight: 3, fillColor: "#14b8a6", fillOpacity: 0.9 })
            .bindTooltip(c.email)
            .addTo(map),
        );
      }
    }
    for (const [id, marker] of markers.current) {
      if (!seen.has(id)) {
        marker.remove();
        markers.current.delete(id);
      }
    }
    if (points.length > 0 && !fitted.current) {
      if (points.length === 1) map.setView(points[0], 15);
      else map.fitBounds(points, { padding: [60, 60] });
      fitted.current = true;
    }
  }, [items, mapError, now]);

  return (
    <div className="space-y-4">
      <Card>
        <CardTitle>Vị trí người lấy mẫu (thời gian thực)</CardTitle>
        <CardDescription>
          Cập nhật mỗi 10 giây. Chỉ hiện người đang bấm Bắt đầu chuyến đi; vị trí tự biến mất sau 2 phút không gửi.
        </CardDescription>
        <div
          ref={mapEl}
          className="mt-4 h-[420px] w-full overflow-hidden rounded-lg border border-slate-200 bg-slate-100"
        />
        {mapError ? <p className="mt-2 text-sm text-red-600">{mapError}</p> : null}
        {error ? <p className="mt-2 text-sm text-red-600">{error}</p> : null}
      </Card>
      <Card>
        <CardTitle>Đang chia sẻ ({items.length})</CardTitle>
        {items.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">Chưa có người lấy mẫu nào đang chia sẻ vị trí.</p>
        ) : (
          <div className="mt-3 overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-slate-500">
                <tr>
                  <th className="py-2 pr-4">Người lấy mẫu</th>
                  <th className="py-2 pr-4">Cập nhật</th>
                  <th className="py-2 pr-4">Sai số</th>
                  <th className="py-2" />
                </tr>
              </thead>
              <tbody>
                {items.map((c) => (
                  <tr key={c.user_id} className="border-t border-slate-100">
                    <td className="py-2 pr-4">{c.email}</td>
                    <td className="py-2 pr-4">{ageText(c.recorded_at, now)}</td>
                    <td className="py-2 pr-4">{c.accuracy_m != null ? `${Math.round(c.accuracy_m)} m` : "—"}</td>
                    <td className="py-2 text-right">
                      <a
                        className="text-teal-700 underline"
                        href={googleMapsUrl(c.latitude, c.longitude)}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Mở trên Google Maps
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
