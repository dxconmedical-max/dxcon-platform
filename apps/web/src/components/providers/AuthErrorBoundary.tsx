"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode; fallbackTitle?: string };
type State = { error: Error | null };

/**
 * Prevents a render crash from leaving a blank / spinning page forever.
 */
export class AuthErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[AuthErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
            <h1 className="text-xl font-semibold text-slate-900">
              {this.props.fallbackTitle ?? "Something went wrong"}
            </h1>
            <p className="mt-2 text-sm text-slate-600" role="alert">
              {this.state.error.message || "Unexpected application error."}
            </p>
            <button
              type="button"
              className="mt-6 rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700"
              onClick={() => {
                this.setState({ error: null });
                window.location.assign("/login");
              }}
            >
              Return to sign in
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
