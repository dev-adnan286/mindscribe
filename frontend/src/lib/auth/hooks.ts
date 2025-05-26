"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuthStore } from "./store";

export function useAuth() {
  const status = useAuthStore((s) => s.status);
  const user = useAuthStore((s) => s.user);
  const login = useAuthStore((s) => s.login);
  const register = useAuthStore((s) => s.register);
  const logout = useAuthStore((s) => s.logout);
  const setUser = useAuthStore((s) => s.setUser);
  return { status, user, login, register, logout, setUser, isAuthenticated: status === "authenticated" };
}

/** Client-side guard used inside the /app layout as a second line of defence after middleware. */
export function useRequireAuth(redirectTo = "/login") {
  const router = useRouter();
  const status = useAuthStore((s) => s.status);
  useEffect(() => {
    if (status === "anonymous") {
      const next = typeof window !== "undefined" ? window.location.pathname : "/app";
      router.replace(`${redirectTo}?next=${encodeURIComponent(next)}`);
    }
  }, [status, router, redirectTo]);
  return status;
}
