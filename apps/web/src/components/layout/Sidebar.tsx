"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { buildNavItems } from "@/lib/navigation";
import { cn } from "@/lib/utils";
import { roleLabel } from "@/lib/roles";
import { useAuth } from "@/hooks/useAuth";

export function Sidebar() {
  const pathname = usePathname();
  const { capabilities, role } = useAuth();
  const items = buildNavItems(capabilities);

  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:flex lg:flex-col">
      <div className="flex h-16 items-center gap-2 border-b border-slate-200 px-5">
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-600 text-white text-sm font-bold">
          Dx
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-900">DxCon</p>
          <p className="text-xs text-slate-500">{roleLabel(role)}</p>
        </div>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {items.map((item) => {
          const Icon = item.icon;
          const active =
            pathname === item.href || pathname.startsWith(`${item.href}/`);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                active
                  ? "bg-teal-50 text-teal-700"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
