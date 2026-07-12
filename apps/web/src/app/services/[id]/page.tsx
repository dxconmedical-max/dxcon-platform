"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { MarketplacePublicShell } from "@/components/marketplace/MarketplacePublicShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { fetchPublicService, type MarketplaceListing } from "@/lib/api/marketplace";

export default function PublicServiceDetailPage() {
  const params = useParams();
  const id = String(params.id ?? "");
  const [item, setItem] = useState<MarketplaceListing | null>(null);

  useEffect(() => {
    void fetchPublicService(id).then((res) => setItem(res.value));
  }, [id]);

  return (
    <MarketplacePublicShell title="Service detail">
      <Link href="/services" className="text-sm text-teal-600">
        ← All services
      </Link>
      {item ? (
        <Card className="mt-4 space-y-3 p-6">
          <h2 className="text-xl font-semibold">{item.title}</h2>
          <p className="text-slate-600">{item.provider?.provider_name}</p>
          <p className="text-lg font-semibold">
            {new Intl.NumberFormat("vi-VN", { style: "currency", currency: item.currency }).format(item.base_price)}
          </p>
          {item.home_collection_available ? (
            <p className="text-sm text-teal-700">Home collection available</p>
          ) : null}
          <Link href={`/app/patient/book?listing=${encodeURIComponent(item.id)}`}>
            <Button>Book this service</Button>
          </Link>
        </Card>
      ) : (
        <p className="mt-4 text-sm text-slate-500">Loading…</p>
      )}
    </MarketplacePublicShell>
  );
}
