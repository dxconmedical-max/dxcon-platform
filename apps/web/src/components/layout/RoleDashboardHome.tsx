"use client";

import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import {
  fetchRoleDashboard,
  type RoleDashboardCard,
  type RoleDashboardKey,
} from "@/lib/api/roleDashboards";
import type { WorkspaceAction } from "@/components/layout/WorkspaceHome";

type Props = {
  title: string;
  subtitle: string;
  role: RoleDashboardKey;
  actions: WorkspaceAction[];
  fallbackCards?: RoleDashboardCard[];
};

const EMPTY_CARDS: RoleDashboardCard[] = [];

export function RoleDashboardHome({
  title,
  subtitle,
  role,
  actions,
  fallbackCards = EMPTY_CARDS,
}: Props) {
  const { accessToken, activeOrganizationId, user } = useAuth();
  const auth = useMemo(
    () => ({
      token: accessToken,
      organizationId: activeOrganizationId,
      collectorId: (user as { collector_id?: string } | null)?.collector_id ?? null,
      patientCode:
        (user as { patient_code?: string } | null)?.patient_code ??
        (user as { patientCode?: string } | null)?.patientCode ??
        null,
    }),
    [accessToken, activeOrganizationId, user],
  );

  const vi = true;
  const CARD_VI: Record<string, string> = {
    "Awaiting collection": "Chờ lấy mẫu",
    "In transit": "Đang vận chuyển",
    "Arrived at lab": "Đã đến phòng XN",
    "Rejected / alerts": "Từ chối / cảnh báo",
    "Orders today": "Đơn hôm nay",
    "Pending collection": "Chờ lấy mẫu",
    "Pending payment": "Chờ thanh toán",
    "Waiting queue": "Hàng chờ",
    "Lab queue": "Hàng đợi xét nghiệm",
    "Ops alerts": "Cảnh báo vận hành",
    "Critical results": "Kết quả nguy kịch",
    "Completed reports": "Báo cáo hoàn tất",
    "Avg TAT (min)": "TAT trung bình (phút)",
    "Overdue tests": "Xét nghiệm trễ hạn",
    Overdue: "Trễ hạn",
    Incoming: "Mẫu đến",
    "Pending validation": "Chờ duyệt",
    "Critical / abnormal": "Nguy kịch / bất thường",
    "Released today": "Đã trả hôm nay",
    Alerts: "Cảnh báo",
    "Pending reviews": "Chờ duyệt kết quả",
    "Critical flags": "Cờ nguy kịch",
    Results: "Kết quả",
    "Orders / visits": "Đơn / lượt khám",
    "Home visits": "Lấy mẫu tại nhà",
    Messages: "Tin nhắn",
  };
  const HINT_VI: Record<string, string> = {
    "Critical + overdue + failed imports": "Nguy kịch + trễ hạn + nhập lỗi",
  };
  const [cards, setCards] = useState<RoleDashboardCard[]>(fallbackCards);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [empty, setEmpty] = useState(false);
  const [generatedAt, setGeneratedAt] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      setError(null);
      setCards(fallbackCards);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRoleDashboard(role, auth);
      setCards(data.cards?.length ? data.cards : fallbackCards);
      setEmpty(Boolean(data.empty));
      setGeneratedAt(data.generated_at ?? null);
    } catch (err) {
      setError(normalizeApiError(err));
      setCards(fallbackCards);
    } finally {
      setLoading(false);
    }
  }, [accessToken, auth, fallbackCards, role]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-teal-50/40 p-6 lg:p-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <Badge tone="info">{vi ? "Hệ thống chính thức" : "Production workspace"}</Badge>
          <Button size="sm" variant="outline" onClick={() => void load()} disabled={loading}>
            {vi ? "Làm mới" : "Refresh"}
          </Button>
        </div>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900 lg:text-3xl">
          {title}
        </h2>
        <p className="mt-2 max-w-2xl text-slate-600">{subtitle}</p>
        {generatedAt ? (
          <p className="mt-2 text-xs text-slate-400">{vi ? "Cập nhật" : "Updated"} {generatedAt}</p>
        ) : null}
      </section>

      {loading ? (
        <p className="text-sm text-slate-500" role="status">
          Đang tải số liệu…
        </p>
      ) : null}

      {error ? (
        <Card className="border-rose-200 bg-rose-50">
          <CardTitle>Không tải được số liệu</CardTitle>
          <CardDescription className="text-rose-700">{error}</CardDescription>
          <Button className="mt-3" size="sm" variant="outline" onClick={() => void load()}>
            Thử lại
          </Button>
        </Card>
      ) : null}

      {!loading && !error && empty ? (
        <p className="rounded-xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
          Chưa có hoạt động nào. Số liệu sẽ hiện sau đơn hàng đầu tiên.
        </p>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => (
          <Card key={card.label}>
            <p className="text-sm text-slate-500">{vi ? (CARD_VI[card.label] ?? card.label) : card.label}</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">
              {loading ? "…" : card.value}
            </p>
            {card.hint ? <p className="mt-1 text-xs text-slate-500">{HINT_VI[card.hint] ?? card.hint}</p> : null}
          </Card>
        ))}
      </section>

      <section>
        <h3 className="mb-4 text-lg font-semibold text-slate-900">{vi ? "Thao tác chính" : "Key actions"}</h3>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {actions.map((action) => (
            <Card key={action.label} className="flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2">
                  <CardTitle>{action.label}</CardTitle>
                  {action.comingSoon ? <Badge>Sắp có</Badge> : null}
                </div>
                {action.description ? (
                  <CardDescription>{action.description}</CardDescription>
                ) : null}
              </div>
              {action.comingSoon ? (
                <span className="mt-4 inline-flex items-center gap-1 text-sm text-slate-400">
                  Đang lên kế hoạch
                </span>
              ) : (
                <Link
                  href={action.href}
                  className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-teal-700 hover:text-teal-800"
                >
                  {vi ? "Mở" : "Open module"}
                  <ArrowRight className="h-4 w-4" />
                </Link>
              )}
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
