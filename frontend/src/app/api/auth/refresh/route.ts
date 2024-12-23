import { NextResponse, type NextRequest } from "next/server";

import {
  REFRESH_COOKIE,
  backendUrl,
  clearRefreshCookie,
  passthroughError,
  proxyAuth,
  sessionResponse,
} from "@/lib/server/auth-cookies";
import type { TokenPair, User } from "@/lib/api/types";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  if (!refreshToken) {
    const response = NextResponse.json({ detail: "No session" }, { status: 401 });
    clearRefreshCookie(response);
    return response;
  }
  const upstream = await proxyAuth("/auth/refresh", { refresh_token: refreshToken });
  if (!upstream.ok) return passthroughError(upstream);
  const tokens = (await upstream.json()) as TokenPair;

  // Include the profile so the client can bootstrap in a single round-trip.
  let user: User | undefined;
  try {
    const me = await fetch(`${backendUrl()}/auth/me`, {
      headers: { Authorization: `Bearer ${tokens.access_token}`, Accept: "application/json" },
      cache: "no-store",
    });
    if (me.ok) user = (await me.json()) as User;
  } catch {
    user = undefined;
  }
  return sessionResponse({ ...tokens, user });
}
