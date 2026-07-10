import type { AuthCapabilities } from "@/services/auth";

export function can(
  capabilities: AuthCapabilities | null,
  permission: string,
): boolean {
  if (!capabilities) return false;
  const perms = capabilities.permissions ?? [];
  if (perms.includes("*")) return true;
  return perms.includes(permission);
}

export function canAny(
  capabilities: AuthCapabilities | null,
  permissions: string[],
): boolean {
  return permissions.some((p) => can(capabilities, p));
}

export function canAll(
  capabilities: AuthCapabilities | null,
  permissions: string[],
): boolean {
  return permissions.every((p) => can(capabilities, p));
}

export function hasFeature(
  capabilities: AuthCapabilities | null,
  feature: string,
): boolean {
  if (!capabilities) return false;
  return (capabilities.features ?? []).includes(feature);
}

export function isWorkspace(
  capabilities: AuthCapabilities | null,
  workspace: string,
): boolean {
  return (capabilities?.workspace ?? "") === workspace;
}

export function isOrganizationType(
  capabilities: AuthCapabilities | null,
  orgType: string,
): boolean {
  return (
    (capabilities?.organization?.organization_type ?? "").toUpperCase() ===
    orgType.toUpperCase()
  );
}
