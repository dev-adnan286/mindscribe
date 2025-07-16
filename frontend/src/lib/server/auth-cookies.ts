/**
 * Server-only helpers for the Next.js auth route handlers.
 * The refresh token is stored in an httpOnly cookie; the browser only ever receives
 * the short-lived access token in the JSON body.
 */

import { NextResponse } from "next/server";

import type { AuthResponse, ClientSession, TokenPair } from "@/lib/api/types";

export const REFRESH_COOKIE = "ms_refresh";
const REFRESH_MAX_AGE_SECONDS = 60 * 60 * 24 * 14;

export function backendUrl(): string {
  const base = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return `${base.replace(/\/$/, "")}/api/v1`;
}

export function setRefreshCookie(response: NextResponse, token: string): void {
  response.cookies.set({
    name: REFRESH_COOKIE,
    value: token,
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: REFRESH_MAX_AGE_SECONDS,
  });
}

export function clearRefreshCookie(response: NextResponse): void {
  response.cookies.set({
    name: REFRESH_COOKIE,
    value: "",
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: 0,
  });
}

/** Forward a JSON body to the backend and pass the status through unchanged. */
export async function proxyAuth(path: string, body: unknown): Promise<Response> {
  return fetch(`${backendUrl()}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
}

export function sessionResponse(data: AuthResponse | (TokenPair & { user?: AuthResponse["user"] })): NextResponse {
  const payload: Partial<ClientSession> = {
    access_token: data.access_token,
    expires_in: data.expires_in,
  };
  if ("user" in data && data.user) payload.user = data.user;
  const response = NextResponse.json(payload);
  setRefreshCookie(response, data.refresh_token);
  return response;
}

export async function passthroughError(upstream: Response): Promise<NextResponse> {
  const contentType = upstream.headers.get("content-type") ?? "application/json";
  const text = await upstream.text();
  const response = new NextResponse(text || JSON.stringify({ detail: "Authentication failed" }), {
    status: upstream.status,
    headers: { "content-type": contentType },
  });
  if (upstream.status === 401) clearRefreshCookie(response);
  return response;
}
