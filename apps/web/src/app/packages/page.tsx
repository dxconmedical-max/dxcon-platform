"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { MarketplacePublicShell } from "@/components/marketplace/MarketplacePublicShell";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { fetchPublicPackages, type MarketplaceListing } from "@/lib/api/marketplace";

export default function PublicPackagesPage() {
  const [q, setQ] = useState("");
  const [listings, setListings] = useState<MarketplaceListing[]>([]);

  useEffect(() => {
    void fetchPublicPackages({ q: q || undefined }).then((res) => setListings(res.value.listings));
  }, [q]);

  return (
    <MarketplacePublicShell title="Health packages">
      <Input className="mb-6 max-w-md" placeholder="Search packages…" value={q} onChange={(e) => setQ(e.target.value)} />
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {listings.map((item) => (
          <Link key={item.id} href={`/packages/${item.id}`}>
            <Card className="p-4 hover:border-teal-300">
              <p className="font-medium">{item.title}</p>
              <p className="mt-2 font-semibold">
                {new Intl.NumberFormat("vi-VN", { style: "currency", currency: item.currency }).format(item.base_price)}
              </p>
            </Card>
          </Link>
        ))}
      </div>
    </MarketplacePublicShell>
  );
}
