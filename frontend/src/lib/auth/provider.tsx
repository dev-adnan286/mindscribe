"use client";

import { useEffect, type ReactNode } from "react";

import { useAuthStore } from "./store";

/** Bootstraps the in-memory access token from the refresh cookie on first load. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const bootstrap = useAuthStore((s) => s.bootstrap);
  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);
  return <>{children}</>;
}
