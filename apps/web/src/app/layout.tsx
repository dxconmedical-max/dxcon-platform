import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";

import { AuthProvider } from "@/components/providers/AuthProvider";
import "@/styles/globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "DxCon — Connected Diagnostics Platform",
    template: "%s | DxCon",
  },
  description:
    "DxCon connects laboratories, clinics, doctors, and patients with secure diagnostics workflows.",
  metadataBase: new URL("https://dxcon.com.vn"),
  applicationName: "DxCon",
  appleWebApp: { capable: true, title: "DxCon", statusBarStyle: "default" },
  icons: { apple: "/icon-192.png" },
  openGraph: {
    type: "website",
    siteName: "DxCon",
    locale: "vi_VN",
    url: "https://dxcon.com.vn",
    title: "DxCon — Nền tảng xét nghiệm y khoa kết nối",
    description:
      "DxCon kết nối phòng xét nghiệm, phòng khám, bác sĩ và bệnh nhân với quy trình xét nghiệm an toàn.",
    images: [{ url: "/icon-512.png", width: 512, height: 512, alt: "DxCon" }],
  },
  twitter: { card: "summary", title: "DxCon", images: ["/icon-512.png"] },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#0f766e",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-white text-slate-900">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
