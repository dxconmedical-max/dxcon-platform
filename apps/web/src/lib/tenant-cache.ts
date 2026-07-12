const tenantCaches = new Set<() => void>();

export function registerTenantCacheClear(handler: () => void): () => void {
  tenantCaches.add(handler);
  return () => tenantCaches.delete(handler);
}

export function clearTenantScopedCaches(): void {
  for (const handler of tenantCaches) {
    handler();
  }
}
