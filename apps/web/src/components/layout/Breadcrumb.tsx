"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LABELS: Record<string, string> = {
  app: "Workspace",
  admin: "Administration",
  executive: "Executive",
  reception: "Reception",
  doctor: "Doctor",
  patient: "Patient",
  lab: "Laboratory",
  collector: "Collector",
  clinic: "Clinic",
  book: "Book",
  bookings: "Bookings",
  orders: "Orders",
  results: "Results",
  payments: "Payments",
  profile: "Profile",
  "health-summary": "Health summary",
  queue: "Queue",
  register: "Walk-in",
  search: "Search",
  route: "Route",
  jobs: "Assigned jobs",
  timeline: "Timeline",
  samples: "Received samples",
  qc: "Quality control",
  verification: "Verification",
  reports: "Reports",
  patients: "Patients",
};

export function Breadcrumb() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length === 0) {
    return null;
  }

  const crumbs = segments.map((segment, index) => {
    const href = `/${segments.slice(0, index + 1).join("/")}`;
    const label = LABELS[segment] ?? segment;
    return { href, label, last: index === segments.length - 1 };
  });

  return (
    <nav aria-label="Breadcrumb" className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
      {crumbs.map((crumb) =>
        crumb.last ? (
          <span key={crumb.href} className="font-medium text-slate-700">
            {crumb.label}
          </span>
        ) : (
          <span key={crumb.href} className="flex items-center gap-1">
            <Link href={crumb.href} className="hover:text-teal-700">
              {crumb.label}
            </Link>
            <span>/</span>
          </span>
        ),
      )}
    </nav>
  );
}
