"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { MarketplacePublicShell } from "@/components/marketplace/MarketplacePublicShell";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { fetchPublicServices, type MarketplaceListing } from "@/lib/api/marketplace";

function formatPrice(value: number, currency = "VND") {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency }).format(value);
}

export default function PublicServicesPage() {
  const [q, setQ] = useState("");
  const [city, setCity] = useState("");
  const [listings, setListings] = useState<MarketplaceListing[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    void fetchPublicServices({ q: q || undefined, city: city || undefined, home_collection: undefined })
      .then((res) => {
        if (!cancelled) {
          setListings(res.value.listings);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [q, city]);

  return (
    <MarketplacePublicShell title="Laboratory tests & services">
      <div className="mb-6 grid gap-3 md:grid-cols-3">
        <Input placeholder="Search tests…" value={q} onChange={(e) => setQ(e.target.value)} />
        <Input placeholder="City" value={city} onChange={(e) => setCity(e.target.value)} />
      </div>
      {loading ? (
        <p className="text-sm text-slate-500">Loading published services…</p>
      ) : listings.length === 0 ? (
        <p className="text-sm text-slate-500">No published services match your filters.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {listings.map((item) => (
            <Link key={item.id} href={`/services/${item.id}`}>
              <Card className="h-full p-4 transition hover:border-teal-300">
                <p className="font-medium text-slate-900">{item.title}</p>
                <p className="mt-1 text-sm text-slate-500">{item.provider?.provider_name}</p>
                <p className="mt-3 font-semibold">{formatPrice(item.base_price, item.currency)}</p>
                {item.turnaround_hours ? (
                  <p className="text-xs text-slate-400">~{item.turnaround_hours}h turnaround</p>
                ) : null}
              </Card>
            </Link>
          ))}
        </div>
      )}
    </MarketplacePublicShell>
  );
}
