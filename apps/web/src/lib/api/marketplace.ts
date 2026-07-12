import { apiRequest } from "./client";
import { withSampleFallback, SAMPLE_NOTE, type Sourced } from "./adapter";

export type MarketplaceListing = {
  id: string;
  listing_code: string;
  title: string;
  base_price: number;
  currency: string;
  home_collection_available?: boolean;
  turnaround_hours?: number;
  service_type?: string;
  service_name?: string;
  category?: string;
  featured?: boolean;
  provider?: {
    id: string;
    provider_name: string;
    provider_type: string;
    city?: string;
    address?: string;
    rating_avg?: number;
  };
};

export type MarketplacePartner = {
  id: string;
  provider_code: string;
  provider_name: string;
  provider_type: string;
  city?: string;
  address?: string;
  featured?: boolean;
  rating_avg?: number;
  turnaround_hours?: number;
};

export type MarketplaceSlot = {
  id: string;
  slot_start: string;
  slot_end: string;
  time: string;
  capacity: number;
  reserved: number;
  available: boolean;
};

export type Quotation = {
  pricing_snapshot_id: string;
  total_amount: number;
  currency: string;
  components: Record<string, unknown>;
};

export type SavedAddress = {
  id: string;
  label: string;
  address_line: string;
  building?: string;
  apartment?: string;
  city?: string;
  collector_notes?: string;
  preferred_window_start?: string;
  preferred_window_end?: string;
};

type SearchParams = {
  q?: string;
  city?: string;
  category?: string;
  home_collection?: boolean;
  featured?: boolean;
  page?: number;
};

export async function fetchPublicServices(params: SearchParams = {}): Promise<Sourced<{ listings: MarketplaceListing[] }>> {
  return withSampleFallback(
    async () => {
      const qs = new URLSearchParams();
      if (params.q) qs.set("q", params.q);
      if (params.city) qs.set("city", params.city);
      if (params.category) qs.set("category", params.category);
      if (params.home_collection) qs.set("home_collection", "true");
      if (params.featured) qs.set("featured", "true");
      const suffix = qs.toString() ? `?${qs}` : "";
      const res = await apiRequest<{ listings: MarketplaceListing[] }>(`/api/v1/marketplace/public/services${suffix}`);
      return { listings: res.listings ?? [] };
    },
    { listings: [] },
    SAMPLE_NOTE,
  );
}

export async function fetchPublicService(id: string): Promise<Sourced<MarketplaceListing>> {
  return withSampleFallback(
    async () => apiRequest<MarketplaceListing>(`/api/v1/marketplace/public/services/${encodeURIComponent(id)}`),
    { id, listing_code: id, title: "Service", base_price: 0, currency: "VND" },
    SAMPLE_NOTE,
  );
}

export async function fetchPublicPackages(params: SearchParams = {}): Promise<Sourced<{ listings: MarketplaceListing[] }>> {
  return withSampleFallback(
    async () => {
      const qs = new URLSearchParams();
      if (params.q) qs.set("q", params.q);
      if (params.city) qs.set("city", params.city);
      const suffix = qs.toString() ? `?${qs}` : "";
      const res = await apiRequest<{ listings: MarketplaceListing[] }>(`/api/v1/marketplace/public/packages${suffix}`);
      return { listings: res.listings ?? [] };
    },
    { listings: [] },
    SAMPLE_NOTE,
  );
}

export async function fetchPublicPackage(id: string): Promise<Sourced<MarketplaceListing>> {
  return fetchPublicService(id);
}

export async function fetchPublicPartners(params: SearchParams = {}): Promise<Sourced<{ partners: MarketplacePartner[] }>> {
  return withSampleFallback(
    async () => {
      const qs = new URLSearchParams();
      if (params.q) qs.set("q", params.q);
      if (params.city) qs.set("city", params.city);
      if (params.category) qs.set("provider_type", params.category);
      const suffix = qs.toString() ? `?${qs}` : "";
      const res = await apiRequest<{ partners: MarketplacePartner[] }>(`/api/v1/marketplace/public/partners${suffix}`);
      return { partners: res.partners ?? [] };
    },
    { partners: [] },
    SAMPLE_NOTE,
  );
}

export async function fetchPublicPartner(id: string): Promise<Sourced<MarketplacePartner>> {
  return withSampleFallback(
    async () => apiRequest<MarketplacePartner>(`/api/v1/marketplace/public/partners/${encodeURIComponent(id)}`),
    { id, provider_code: id, provider_name: "Partner", provider_type: "LABORATORY" },
    SAMPLE_NOTE,
  );
}

export async function fetchProviderSlots(
  providerId: string,
  date: string,
  organizationId?: string,
): Promise<Sourced<{ slots: MarketplaceSlot[] }>> {
  return withSampleFallback(
    async () => {
      const qs = new URLSearchParams({ date });
      const res = await apiRequest<{ slots: MarketplaceSlot[] }>(
        `/api/v1/marketplace/providers/${encodeURIComponent(providerId)}/slots?${qs}`,
        { organizationId },
      );
      return { slots: res.slots ?? [] };
    },
    { slots: [] },
    SAMPLE_NOTE,
  );
}

export async function fetchQuotation(listingId: string, promotionCode?: string): Promise<Sourced<Quotation>> {
  return withSampleFallback(
    async () =>
      apiRequest<Quotation>("/api/v1/marketplace/catalog/quote", {
        method: "POST",
        body: { listing_id: listingId, promotion_code: promotionCode },
      }),
    { pricing_snapshot_id: "sample", total_amount: 0, currency: "VND", components: {} },
    SAMPLE_NOTE,
  );
}
