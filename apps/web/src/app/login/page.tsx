"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useRef, useState, Suspense } from "react";
import { Activity, Eye, EyeOff } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { DEMO_MODE } from "@/lib/constants";
import { loginErrorMessage } from "@/lib/errors";
import { safeRedirectPath } from "@/lib/urls";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, error, clearError, isAuthenticated, workspacePath, isHydrated } =
    useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  // Submit-only flag. Never bind the button to auth bootstrap / isLoading /
  // status==="loading" — that leaves "Signing in..." stuck on first paint.
  const [isSubmittingLogin, setIsSubmittingLogin] = useState(false);
  const submittingRef = useRef(false);
  const [formError, setFormError] = useState<string | null>(
    searchParams.get("reason") === "session-expired"
      ? "Your session has expired. Please sign in again."
      : null,
  );

  const emailValid = email.trim().length > 0 && email.includes("@");
  const passwordValid = password.length > 0;
  const canSubmit = emailValid && passwordValid && !isSubmittingLogin;

  useEffect(() => {
    if (!isHydrated) return;
    if (isAuthenticated) {
      router.replace(safeRedirectPath(searchParams.get("next"), workspacePath));
    }
  }, [isAuthenticated, isHydrated, workspacePath, router, searchParams]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    console.debug("[login] handleSubmit start", {
      canSubmit,
      isSubmittingLogin,
      email: email.trim(),
    });
    if (!canSubmit || isSubmittingLogin || submittingRef.current) {
      console.debug("[login] handleSubmit blocked (duplicate or invalid)");
      return;
    }
    submittingRef.current = true;
    clearError();
    setFormError(null);
    setIsSubmittingLogin(true);
    try {
      console.debug("[login] calling authStore.login() → POST /api/v1/auth/login");
      const { redirect } = await login(email.trim(), password, remember);
      console.debug("[login] authStore.login() resolved", { redirect });
      router.replace(safeRedirectPath(searchParams.get("next"), redirect));
    } catch (err) {
      console.debug("[login] authStore.login() rejected", err);
      setFormError(loginErrorMessage(err));
    } finally {
      console.debug("[login] handleSubmit finally → isSubmittingLogin=false");
      submittingRef.current = false;
      setIsSubmittingLogin(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      <div className="hidden w-1/2 bg-gradient-to-br from-slate-950 via-slate-900 to-teal-900 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500">
              <Activity className="h-5 w-5" />
            </span>
            <span className="text-xl font-semibold">DxCon</span>
          </div>
          <h1 className="mt-16 text-4xl font-semibold leading-tight">
            Sign in to your workspace
          </h1>
          <p className="mt-4 max-w-md text-slate-300">
            Authenticate against api.dxcon.com.vn with your organization credentials.
          </p>
        </div>
        <p className="text-sm text-slate-400">Production API gateway</p>
      </div>
      <div className="flex flex-1 items-center justify-center bg-slate-50 px-4 py-12">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="text-2xl font-semibold text-slate-900">Sign in</h2>
          <p className="mt-1 text-sm text-slate-600">Use your DxCon account.</p>
          {DEMO_MODE ? (
            <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800">
              Demo mode is enabled — not for production use.
            </p>
          ) : null}
          <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pr-10"
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 text-slate-600">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                />
                Remember me
              </label>
              <Link href="/forgot-password" className="text-teal-700 hover:text-teal-800">
                Need help signing in?
              </Link>
            </div>
            {(formError || error) && (
              <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
                {formError || error}
              </p>
            )}
            <Button type="submit" className="w-full" disabled={!canSubmit}>
              {isSubmittingLogin ? "Signing in..." : "Sign in"}
            </Button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-500">
            <Link href="/register" className="text-teal-700">
              Create account
            </Link>
            {" · "}
            <Link href="/" className="text-teal-700">
              Back to homepage
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center">Loading...</div>
      }
    >
      <LoginForm />
    </Suspense>
  );
}
