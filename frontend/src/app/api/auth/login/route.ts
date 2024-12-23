import { NextResponse, type NextRequest } from "next/server";

import { passthroughError, proxyAuth, sessionResponse } from "@/lib/server/auth-cookies";
import type { AuthResponse } from "@/lib/api/types";

export async function POST(request: NextRequest): Promise<NextResponse> {
  const body = await request.json().catch(() => null);
  if (!body || typeof body !== "object") {
    return NextResponse.json({ detail: "Invalid request body" }, { status: 400 });
  }
  const upstream = await proxyAuth("/auth/login", body);
  if (!upstream.ok) return passthroughError(upstream);
  return sessionResponse((await upstream.json()) as AuthResponse);
}
