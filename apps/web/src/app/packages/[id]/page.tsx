"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { MarketplacePublicShell } from "@/components/marketplace/MarketplacePublicShell";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { fetchPublicPackage, type MarketplaceListing } from "@/lib/api/marketplace";

export default function PublicPackageDetailPage() {
  const params = useParams();
  const id = String(params.id ?? "");
  const [item, setItem] = useState<MarketplaceListing | null>(null);

  useEffect(() => {
    void fetchPublicPackage(id).then((res) => setItem(res.value));
  }, [id]);

  return (
    <MarketplacePublicShell title="Package detail">
      <Link href="/packages" className="text-sm text-teal-600">
        ← All packages
      </Link>
      {item ? (
        <Card className="mt-4 space-y-3 p-6">
          <h2 className="text-xl font-semibold">{item.title}</h2>
          <p className="text-lg font-semibold">
            {new Intl.NumberFormat("vi-VN", { style: "currency", currency: item.currency }).format(item.base_price)}
          </p>
          <Link href={`/app/patient/book?listing=${encodeURIComponent(item.id)}`}>
            <Button>Book package</Button>
          </Link>
        </Card>
      ) : null}
    </MarketplacePublicShell>
  );
}
