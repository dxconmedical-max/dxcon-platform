import { AppShell } from "@/components/layout/AppShell";
import { WorkspaceHome } from "@/components/layout/WorkspaceHome";

export const metadata = { title: "Customer Onboarding" };

export default function AdminOnboardingPage() {
  return (
    <AppShell title="Onboarding" workspacePath="/app/admin/onboarding">
      <WorkspaceHome
        title="Customer onboarding wizard"
        subtitle="Laboratory, clinic, hospital, doctor, collector company, and corporate onboarding."
        statusCards={[
          { label: "Flow", value: "10 steps" },
          { label: "API", value: "/pilot-readiness/onboarding" },
          { label: "Partner reg", value: "Admin review" },
          { label: "Activation", value: "Server-side" },
        ]}
        actions={[
          {
            label: "Start laboratory onboarding",
            href: "/onboarding/register",
            description: "Self-service partner registration for clinics and labs.",
          },
          {
            label: "Organization setup",
            href: "/app/admin/organizations",
            description: "Logo, theme, departments, services wizard.",
          },
          {
            label: "Master data import",
            href: "/app/admin",
            description: "CSV/Excel import via MDM (Flask admin).",
          },
        ]}
      />
    </AppShell>
  );
}
