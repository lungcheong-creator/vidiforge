/** Banner shown on first load if no API token is set. */

"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { setToken } from "@/lib/api";

export function TokenGate({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [token, setLocalToken] = useState<string>("");
  const [mounted, setMounted] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const t = window.localStorage.getItem("vf_api_token");
    if (t) setSaved(true);
    setMounted(true);
  }, []);

  if (!mounted) return null;

  // If user already has a token, render children
  if (saved && typeof window !== "undefined" && window.localStorage.getItem("vf_api_token")) {
    return <>{children}</>;
  }

  // On /setup page, just render children (so the form is visible)
  if (pathname === "/setup") {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <div className="w-full max-w-lg rounded-sm border border-border bg-card p-10 space-y-6">
        <div className="space-y-2">
          <p className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">First time</p>
          <h1 className="font-display text-3xl font-medium tracking-tight">
            Welcome to <span className="italic text-primary">VidiForge</span>.
          </h1>
          <p className="font-display italic text-muted-foreground">
            Enter the bearer token you set as <code className="font-mono">VIDIFORGE_API_TOKEN</code> when launching the API.
          </p>
        </div>
        <div className="space-y-3">
          <label className="font-display text-[10px] uppercase tracking-[0.2em] text-muted-foreground">
            API Token
          </label>
          <input
            type="password"
            value={token}
            onChange={(e) => setLocalToken(e.target.value)}
            placeholder="your-secret-token"
            className="h-11 w-full border border-border bg-background px-4 font-mono text-sm focus:outline-none focus:border-primary/50"
          />
        </div>
        <button
          disabled={token.length < 8}
          onClick={() => {
            setToken(token);
            window.location.reload();
          }}
          className="w-full h-11 rounded-full bg-primary text-primary-foreground font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors"
        >
          Continue →
        </button>
        <p className="text-xs text-muted-foreground">
          The token is stored only in localStorage and sent as <code className="font-mono">Authorization: Bearer ...</code> on every request.
        </p>
      </div>
    </div>
  );
}