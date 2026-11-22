"use client";

import { useEffect, useRef, useState } from "react";

import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { fetchCollectors, googleMapsUrl, type LiveCollector } from "@/lib/api/liveLocation";
import { normalizeApiError } from "@/lib/errors";
import { useAuthStore } from "@/stores/authStore";

const POLL_MS = 10000;
const MAPS_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY ?? "";

type LatLng = { lat: number; lng: number };
type GMarker = { setPosition: (p: LatLng) => void; setMap: (m: GMap | null) => void };
type GBounds = { extend: (p: LatLng) => void };
type GMap = {
  fitBounds: (b: GBounds, padding?: number) => void;
  setCenter: (p: LatLng) => void;
  setZoom: (z: number) => void;
};
type GoogleMaps = {
  Map: new (el: HTMLElement, opts: Record<string, unknown>) => GMap;
  Marker: new (opts: Record<string, unknown>) => GMarker;
  LatLngBounds: new () => GBounds;
};
type WindowWithGoogle = Window & { google?: { maps?: GoogleMaps } };

let loader: Promise<GoogleMaps> | null = null;

function loadGoogleMaps(): Promise<GoogleMaps> {
  const w = window as WindowWithGoogle;
  if (w.google?.maps?.Map) return Promise.resolve(w.google.maps);
  if (loader) return loader;
  loader = new Promise<GoogleMaps>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(MAPS_KEY)}&v=weekly`;
    script.async = true;
    script.onload = () => {
      const maps = (window as WindowWithGoogle).google?.maps;
      if (maps) resolve(maps);
      else reject(new Error("Google Maps không tải được."));
    };
    script.onerror = () => reject(new Error("Google Maps không tải được."));
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
  const mapRef = useRef<GMap | null>(null);
  const mapsRef = useRef<GoogleMaps | null>(null);
  const markers = useRef<Map<string, GMarker>>(new Map());
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
    if (!MAPS_KEY || !mapEl.current) return;
    let cancelled = false;
    loadGoogleMaps()
      .then((maps) => {
        if (cancelled || !mapEl.current || mapRef.current) return;
        mapsRef.current = maps;
        mapRef.current = new maps.Map(mapEl.current, {
          center: { lat: 10.7769, lng: 106.7009 },
          zoom: 11,
          mapTypeControl: false,
          streetViewControl: false,
        });
      })
      .catch((err: unknown) => setMapError(err instanceof Error ? err.message : "Lỗi bản đồ."));
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const maps = mapsRef.current;
    const map = mapRef.current;
    if (!maps || !map) return;
    const seen = new Set<string>();
    const bounds = new maps.LatLngBounds();
    for (const c of items) {
      const pos = { lat: c.latitude, lng: c.longitude };
      seen.add(c.user_id);
      bounds.extend(pos);
      const existing = markers.current.get(c.user_id);
      if (existing) existing.setPosition(pos);
      else markers.current.set(c.user_id, new maps.Marker({ position: pos, map, title: c.email }));
    }
    for (const [id, marker] of markers.current) {
      if (!seen.has(id)) {
        marker.setMap(null);
        markers.current.delete(id);
      }
    }
    if (items.length > 0 && !fitted.current) {
      if (items.length === 1) {
        map.setCenter({ lat: items[0].latitude, lng: items[0].longitude });
        map.setZoom(15);
      } else {
        map.fitBounds(bounds, 60);
      }
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
        {MAPS_KEY ? (
          <div
            ref={mapEl}
            className="mt-4 h-[420px] w-full overflow-hidden rounded-lg border border-slate-200 bg-slate-100"
          />
        ) : (
          <p className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-slate-800">
            Chưa cấu hình khóa Google Maps nên chưa hiện bản đồ. Danh sách bên dưới vẫn dùng được, bấm &quot;Mở trên
            Google Maps&quot; để xem từng vị trí.
          </p>
        )}
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
