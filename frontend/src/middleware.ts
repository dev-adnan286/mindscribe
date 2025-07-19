import { NextResponse, type NextRequest } from "next/server";

const REFRESH_COOKIE = "ms_refresh";
const PROTECTED_PREFIX = "/app";
const AUTH_PAGES = new Set(["/login", "/register"]);

/**
 * Edge guard: the presence of the refresh cookie is a cheap signal of a session.
 * The API still validates every request, and the /app layout re-checks on the client.
 */
export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const hasSession = Boolean(request.cookies.get(REFRESH_COOKIE)?.value);

  if (pathname.startsWith(PROTECTED_PREFIX) && !hasSession) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.search = `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }

  if (AUTH_PAGES.has(pathname) && hasSession) {
    const url = request.nextUrl.clone();
    url.pathname = "/app";
    url.search = "";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/app/:path*", "/login", "/register"],
};
