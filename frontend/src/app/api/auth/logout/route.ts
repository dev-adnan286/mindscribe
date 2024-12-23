import { NextResponse, type NextRequest } from "next/server";

import { REFRESH_COOKIE, clearRefreshCookie, proxyAuth } from "@/lib/server/auth-cookies";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const refreshToken = request.cookies.get(REFRESH_COOKIE)?.value;
  if (refreshToken) {
    // Best effort: revoke server-side; the cookie is cleared regardless.
    await proxyAuth("/auth/logout", { refresh_token: refreshToken }).catch(() => undefined);
  }
  const response = new NextResponse(null, { status: 204 });
  clearRefreshCookie(response);
  return response;
}
