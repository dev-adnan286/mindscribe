"use client";

import { create } from "zustand";

import { authApi, tokenStore, refreshAccessToken, type User } from "@/lib/api";

export type AuthStatus = "loading" | "authenticated" | "anonymous";

interface AuthState {
  status: AuthStatus;
  user: User | null;
  bootstrap: () => Promise<void>;
  login: (email: string, password: string) => Promise<User>;
  register: (email: string, password: string, name: string) => Promise<User>;
  logout: () => Promise<void>;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  status: "loading",
  user: null,

  async bootstrap() {
    if (get().status !== "loading") return;
    const token = await refreshAccessToken();
    if (!token) {
      set({ status: "anonymous", user: null });
      return;
    }
    try {
      const user = await authApi.me();
      set({ status: "authenticated", user });
    } catch {
      tokenStore.set(null);
      set({ status: "anonymous", user: null });
    }
  },

  async login(email, password) {
    const session = await authApi.login(email, password);
    tokenStore.set(session.access_token);
    set({ status: "authenticated", user: session.user });
    return session.user;
  },

  async register(email, password, name) {
    const session = await authApi.register(email, password, name);
    tokenStore.set(session.access_token);
    set({ status: "authenticated", user: session.user });
    return session.user;
  },

  async logout() {
    await authApi.logout();
    tokenStore.set(null);
    set({ status: "anonymous", user: null });
  },

  setUser(user) {
    set({ user });
  },
}));
