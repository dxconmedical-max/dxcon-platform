"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

export default function LogoutPage() {
  const router = useRouter();
  const { logout } = useAuth();

  useEffect(() => {
    void logout().then(() => router.replace("/login"));
  }, [logout, router]);

  return (
    <div className="flex min-h-screen items-center justify-center text-slate-600">
      Signing out...
    </div>
  );
}
