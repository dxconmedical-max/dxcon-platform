"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { sendPing, stopSharing } from "@/lib/api/liveLocation";
import { normalizeApiError } from "@/lib/errors";
import { useAuthStore } from "@/stores/authStore";

const SEND_EVERY_MS = 15000;

type WakeLockSentinelLike = { release: () => Promise<void> };
type NavigatorWithWakeLock = Navigator & {
  wakeLock?: { request: (type: "screen") => Promise<WakeLockSentinelLike> };
};

export function ShareLocation() {
  const token = useAuthStore((s) => s.accessToken);
  const organizationId = useAuthStore((s) => s.activeOrganizationId);
  const [active, setActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSent, setLastSent] = useState<Date | null>(null);
  const watchId = useRef<number | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const latest = useRef<GeolocationCoordinates | null>(null);
  const wakeLock = useRef<WakeLockSentinelLike | null>(null);
  const tokenRef = useRef(token);
  const orgRef = useRef(organizationId);

  useEffect(() => {
    tokenRef.current = token;
    orgRef.current = organizationId;
  }, [token, organizationId]);

  const flush = useCallback(async () => {
    const c = latest.current;
    if (!c) return;
    try {
      await sendPing(
        { token: tokenRef.current, organizationId: orgRef.current },
        {
          latitude: c.latitude,
          longitude: c.longitude,
          accuracy_m: c.accuracy ?? undefined,
          heading: c.heading ?? undefined,
          speed_kmh: c.speed != null ? c.speed * 3.6 : undefined,
        },
      );
      setLastSent(new Date());
      setError(null);
    } catch (err) {
      setError(normalizeApiError(err));
    }
  }, []);

  const halt = useCallback(async (notifyServer: boolean) => {
    if (watchId.current !== null) {
      navigator.geolocation.clearWatch(watchId.current);
      watchId.current = null;
    }
    if (timer.current) {
      clearInterval(timer.current);
      timer.current = null;
    }
    try {
      await wakeLock.current?.release();
    } catch {
      /* ignore */
    }
    wakeLock.current = null;
    latest.current = null;
    setActive(false);
    if (notifyServer) {
      try {
        await stopSharing({ token: tokenRef.current, organizationId: orgRef.current });
      } catch {
        /* the server drops the position by itself after about 2 minutes */
      }
    }
  }, []);

  async function start() {
    setError(null);
    if (!("geolocation" in navigator)) {
      setError("Thiết bị này không hỗ trợ định vị.");
      return;
    }
    try {
      wakeLock.current =
        (await (navigator as NavigatorWithWakeLock).wakeLock?.request("screen")) ?? null;
    } catch {
      wakeLock.current = null;
    }
    watchId.current = navigator.geolocation.watchPosition(
      (pos) => {
        const first = latest.current === null;
        latest.current = pos.coords;
        if (first) void flush();
      },
      (err) => {
        setError(
          err.code === err.PERMISSION_DENIED
            ? "Bạn chưa cho phép định vị. Vào cài đặt trình duyệt, cho phép vị trí cho dxcon.com.vn rồi thử lại."
            : "Không lấy được vị trí. Kiểm tra GPS và mạng.",
        );
        void halt(false);
      },
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 20000 },
    );
    timer.current = setInterval(() => void flush(), SEND_EVERY_MS);
    setActive(true);
  }

  useEffect(() => {
    return () => {
      void halt(true);
    };
  }, [halt]);

  return (
    <Card>
      <CardTitle>Chia sẻ vị trí khi đi lấy mẫu</CardTitle>
      <CardDescription>
        Chỉ nhân viên DxCon thấy vị trí của bạn, và chỉ khi bạn bấm Bắt đầu. Vị trí tự xóa sau 2 phút kể từ lần gửi
        cuối, hệ thống không lưu lịch sử di chuyển. Giữ màn hình sáng và trang này mở trong lúc đi.
      </CardDescription>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        {active ? (
          <Button variant="secondary" onClick={() => void halt(true)}>
            Dừng chia sẻ
          </Button>
        ) : (
          <Button onClick={() => void start()}>Bắt đầu chuyến đi</Button>
        )}
        {active ? (
          <span className="text-sm text-teal-700">
            Đang chia sẻ{lastSent ? ` · gửi lúc ${lastSent.toLocaleTimeString("vi-VN")}` : " · đang lấy vị trí…"}
          </span>
        ) : null}
        {error ? <span className="text-sm text-red-600">{error}</span> : null}
      </div>
    </Card>
  );
}
