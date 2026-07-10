import type { Metadata } from "next";

export const metadata: Metadata = {
  title: { default: "Workspace", template: "%s | DxCon" },
};

export default function AppWorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
