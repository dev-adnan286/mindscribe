/**
 * Typed fetch wrapper for the MindScribe API.
 *
 * Auth model (see README "Authentication"):
 *  - The short-lived access token lives only in memory (`tokenStore`), never in storage.
 *  - The refresh token lives in an httpOnly cookie owned by the Next.js route handlers
 *    under /api/auth/*; the browser JS never sees it.
 *  - On a 401 the client calls POST /api/auth/refresh (same origin, cookie attached),
 *    swaps the in-memory access token and retries the original request exactly once.
 *    Concurrent 401s share a single in-flight refresh.
 */

import type { ClientSession, Problem } from "./types";

export const API_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");
export const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  readonly problem: Problem | null;

  constructor(status: number, message: string, problem: Problem | null = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
  }

  get fieldErrors(): Record<string, string> {
    const map: Record<string, string> = {};
    for (const err of this.problem?.errors ?? []) {
      const field = err.loc[err.loc.length - 1];
      if (field && !map[field]) map[field] = err.msg;
    }
    return map;
  }
}

type Listener = (token: string | null) => void;

class TokenStore {
  private token: string | null = null;
  private listeners = new Set<Listener>();

  get(): string | null {
    return this.token;
  }

  set(token: string | null): void {
    this.token = token;
    this.listeners.forEach((listener) => listener(token));
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
}

export const tokenStore = new TokenStore();

let refreshInFlight: Promise<string | null> | null = null;

/** Ask the Next.js route handler to rotate the refresh cookie and hand back a new access token. */
export async function refreshAccessToken(fetchImpl: typeof fetch = fetch): Promise<string | null> {
  if (refreshInFlight) return refreshInFlight;
  refreshInFlight = (async () => {
    try {
      const response = await fetchImpl("/api/auth/refresh", {
        method: "POST",
        credentials: "include",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) {
        tokenStore.set(null);
        return null;
      }
      const session = (await response.json()) as ClientSession;
      tokenStore.set(session.access_token);
      return session.access_token;
    } catch {
      tokenStore.set(null);
      return null;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined | null>;
  auth?: boolean;
  signal?: AbortSignal;
  /** Injectable for tests. */
  fetchImpl?: typeof fetch;
}

export function buildUrl(path: string, query?: RequestOptions["query"]): string {
  const url = new URL(`${API_PREFIX}${path}`, API_URL);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, String(value));
    }
  }
  return url.toString();
}

async function parseProblem(response: Response): Promise<Problem | null> {
  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.includes("json")) return null;
  try {
    return (await response.json()) as Problem;
  } catch {
    return null;
  }
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, query, auth = true, signal, fetchImpl = fetch } = options;

  const doFetch = async (token: string | null): Promise<Response> => {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (auth && token) headers.Authorization = `Bearer ${token}`;
    return fetchImpl(buildUrl(path, query), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal,
    });
  };

  let response = await doFetch(tokenStore.get());

  if (response.status === 401 && auth) {
    const fresh = await refreshAccessToken(fetchImpl);
    if (fresh) response = await doFetch(fresh);
  }

  if (!response.ok) {
    const problem = await parseProblem(response);
    const message = problem?.detail ?? problem?.title ?? `Request failed with status ${response.status}`;
    throw new ApiError(response.status, message, problem);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string, query?: RequestOptions["query"], options?: RequestOptions) =>
    request<T>(path, { ...options, method: "GET", query }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "POST", body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: "PATCH", body }),
  delete: <T = void>(path: string, options?: RequestOptions) => request<T>(path, { ...options, method: "DELETE" }),
};
