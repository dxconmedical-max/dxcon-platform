"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { MarketplacePublicShell } from "@/components/marketplace/MarketplacePublicShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { fetchPublicPartner, type MarketplacePartner } from "@/lib/api/marketplace";

export default function PublicPartnerDetailPage() {
  const params = useParams();
  const id = String(params.id ?? "");
  const [partner, setPartner] = useState<MarketplacePartner | null>(null);

  useEffect(() => {
    void fetchPublicPartner(id).then((res) => setPartner(res.value));
  }, [id]);

  return (
    <MarketplacePublicShell title="Partner profile">
      <Link href="/partners" className="text-sm text-teal-600">
        ← All partners
      </Link>
      {partner ? (
        <Card className="mt-4 space-y-2 p-6">
          <h2 className="text-xl font-semibold">{partner.provider_name}</h2>
          <p className="text-slate-600">{partner.provider_type}</p>
          {partner.address ? <p className="text-sm">{partner.address}</p> : null}
          <Link href={`/app/patient/book?provider=${encodeURIComponent(partner.id)}`}>
            <Button className="mt-4">Book with this partner</Button>
          </Link>
        </Card>
      ) : null}
    </MarketplacePublicShell>
  );
}
