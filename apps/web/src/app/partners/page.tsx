"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { MarketplacePublicShell } from "@/components/marketplace/MarketplacePublicShell";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { fetchPublicPartners, type MarketplacePartner } from "@/lib/api/marketplace";

export default function PublicPartnersPage() {
  const [q, setQ] = useState("");
  const [city, setCity] = useState("");
  const [partners, setPartners] = useState<MarketplacePartner[]>([]);

  useEffect(() => {
    void fetchPublicPartners({ q: q || undefined, city: city || undefined, featured: false }).then((res) =>
      setPartners(res.value.partners),
    );
  }, [q, city]);

  return (
    <MarketplacePublicShell title="Healthcare partners">
      <div className="mb-6 grid gap-3 md:grid-cols-2">
        <Input placeholder="Search partners…" value={q} onChange={(e) => setQ(e.target.value)} />
        <Input placeholder="City" value={city} onChange={(e) => setCity(e.target.value)} />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {partners.map((p) => (
          <Link key={p.id} href={`/partners/${p.id}`}>
            <Card className="p-4 hover:border-teal-300">
              <p className="font-medium">{p.provider_name}</p>
              <p className="text-sm text-slate-500">{p.provider_type}</p>
              {p.city ? <p className="text-xs text-slate-400">{p.city}</p> : null}
            </Card>
          </Link>
        ))}
      </div>
    </MarketplacePublicShell>
  );
}
