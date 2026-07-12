"use client";

import Link from "next/link";
import { Bell, ChevronDown, LogOut, Menu, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { buildNavItems } from "@/lib/navigation";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Breadcrumb } from "@/components/layout/Breadcrumb";
import { useAuth } from "@/hooks/useAuth";
import { roleLabel } from "@/lib/roles";

export function Header({
  title,
  workspaceLabel,
  onMenuClick,
}: {
  title: string;
  workspaceLabel?: string;
  onMenuClick?: () => void;
}) {
  const router = useRouter();
  const { user, role, logout, memberships, activeOrganizationId, selectOrganization, capabilities } =
    useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const activeOrg = capabilities?.organization;

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
      <div className="flex h-16 items-center justify-between gap-4 px-4 lg:px-6">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onMenuClick}
              className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="min-w-0">
              <h1 className="truncate text-lg font-semibold text-slate-900">
                {title}
              </h1>
              {workspaceLabel && workspaceLabel !== title ? (
                <p className="truncate text-xs text-slate-500">{workspaceLabel}</p>
              ) : null}
              <Breadcrumb />
            </div>
          </div>
        </div>

        <div className="hidden items-center gap-3 md:flex">
          {memberships.length > 1 ? (
            <select
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm"
              value={activeOrganizationId ?? ""}
              onChange={(event) => {
                void selectOrganization(event.target.value).then((path) =>
                  router.push(path),
                );
              }}
              aria-label="Switch organization"
            >
              {memberships.map((m) => (
                <option key={m.organization_id} value={m.organization_id}>
                  {m.organization_name}
                </option>
              ))}
            </select>
          ) : activeOrg ? (
            <span className="text-sm text-slate-600">{activeOrg.organization_name}</span>
          ) : null}
          <div className="relative hidden lg:block">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              placeholder="Search modules..."
              className="w-48 rounded-lg border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm outline-none focus:border-teal-500"
            />
          </div>
          <Badge tone="info">{roleLabel(role)}</Badge>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            className="relative rounded-lg p-2 text-slate-500 hover:bg-slate-100"
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5" />
          </button>
          <div className="relative">
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-1.5 text-sm hover:bg-slate-50"
            >
              <span className="hidden max-w-[140px] truncate sm:inline">
                {user?.email ?? "Account"}
              </span>
              <ChevronDown className="h-4 w-4 text-slate-400" />
            </button>
            {menuOpen ? (
              <div className="absolute right-0 mt-2 w-48 rounded-xl border border-slate-200 bg-white p-2 shadow-lg">
                <Button
                  variant="ghost"
                  size="sm"
                  className="w-full justify-start"
                  onClick={() =>
                    void logout().then(() => router.push("/login"))
                  }
                >
                  <LogOut className="h-4 w-4" />
                  Sign out
                </Button>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </header>
  );
}

export function MobileNav() {
  const { capabilities } = useAuth();
  const items = buildNavItems(capabilities).slice(0, 5);
  return (
    <div className="border-t border-slate-200 bg-white px-4 py-3 lg:hidden">
      <div className="flex gap-2 overflow-x-auto">
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="whitespace-nowrap rounded-full border border-slate-200 px-3 py-1 text-xs font-medium text-slate-600"
          >
            {item.label}
          </Link>
        ))}
      </div>
    </div>
  );
}
