import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, buildUrl, request, tokenStore } from "@/lib/api/client";

function jsonResponse(body: unknown, status = 200, contentType = "application/json"): Response {
  return new Response(body === undefined ? null : JSON.stringify(body), {
    status,
    headers: { "content-type": contentType },
  });
}

describe("buildUrl", () => {
  it("prefixes the API path and drops empty query params", () => {
    const url = buildUrl("/notes", { page: 2, q: "", tag: undefined, sort: "title_asc" });
    expect(url).toBe("http://localhost:8000/api/v1/notes?page=2&sort=title_asc");
  });
});

describe("request", () => {
  beforeEach(() => {
    tokenStore.set("access-1");
  });
  afterEach(() => {
    tokenStore.set(null);
    vi.restoreAllMocks();
  });

  it("attaches the bearer token and parses JSON", async () => {
    const fetchImpl = vi.fn(async () => jsonResponse({ id: "n1" }));
    const result = await request<{ id: string }>("/notes/n1", { fetchImpl });
    expect(result).toEqual({ id: "n1" });
    const [url, init] = fetchImpl.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/v1/notes/n1");
    expect((init.headers as Record<string, string>).Authorization).toBe("Bearer access-1");
  });

  it("refreshes once on 401 and retries with the new token", async () => {
    const fetchImpl = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url === "/api/auth/refresh") return jsonResponse({ access_token: "access-2", expires_in: 1800 });
      const calls = fetchImpl.mock.calls.filter(([i]) => String(i) !== "/api/auth/refresh").length;
      return calls === 1 ? jsonResponse({ detail: "expired" }, 401) : jsonResponse({ ok: true });
    });
    const result = await request<{ ok: boolean }>("/auth/me", { fetchImpl });
    expect(result).toEqual({ ok: true });
    expect(tokenStore.get()).toBe("access-2");
    expect(fetchImpl).toHaveBeenCalledTimes(3);
    const retry = fetchImpl.mock.calls[2] as unknown as [string, RequestInit];
    expect((retry[1].headers as Record<string, string>).Authorization).toBe("Bearer access-2");
  });

  it("throws ApiError and clears the token when refresh fails", async () => {
    const fetchImpl = vi.fn(async (input: RequestInfo | URL) => {
      if (String(input) === "/api/auth/refresh") return jsonResponse({ detail: "No session" }, 401);
      return jsonResponse({ title: "Unauthorized", status: 401, detail: "Token has expired", type: "x" }, 401, "application/problem+json");
    });
    await expect(request("/auth/me", { fetchImpl })).rejects.toMatchObject({ status: 401, message: "Token has expired" });
    expect(tokenStore.get()).toBeNull();
  });

  it("exposes field errors from RFC7807 validation problems", async () => {
    const problem = {
      type: "x",
      title: "Validation Failed",
      status: 422,
      detail: "Request validation failed",
      errors: [{ loc: ["body", "email"], msg: "value is not a valid email address", type: "value_error" }],
    };
    const fetchImpl = vi.fn(async () => jsonResponse(problem, 422, "application/problem+json"));
    try {
      await request("/auth/register", { method: "POST", body: {}, auth: false, fetchImpl });
      throw new Error("should have thrown");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).fieldErrors).toEqual({ email: "value is not a valid email address" });
    }
  });

  it("returns undefined for 204 responses", async () => {
    const fetchImpl = vi.fn(async () => new Response(null, { status: 204 }));
    await expect(request("/notes/n1", { method: "DELETE", fetchImpl })).resolves.toBeUndefined();
  });
});
