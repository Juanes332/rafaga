import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiClient, configureApiClient } from "@/lib/http/api-client";
import { ApiError } from "@/lib/http/api-error";
import { server } from "../../msw/server";
import { API } from "../../msw/api-base";

describe("apiClient", () => {
  const onUnauthorized = vi.fn();
  beforeEach(() => {
    onUnauthorized.mockReset();
    configureApiClient({ baseUrl: API, getToken: () => "tok", onUnauthorized });
  });

  it("sends the bearer token and parses JSON", async () => {
    server.use(http.get(`${API}/echo`, ({ request }) => HttpResponse.json({ auth: request.headers.get("authorization") })));
    await expect(apiClient.get<{ auth: string }>("/echo")).resolves.toEqual({ auth: "Bearer tok" });
  });

  it("serialises query params, skipping undefined", async () => {
    server.use(http.get(`${API}/q`, ({ request }) => HttpResponse.json({ s: new URL(request.url).search })));
    await expect(apiClient.get<{ s: string }>("/q", { query: { a: 1, b: undefined, c: "x y" } })).resolves.toEqual({ s: "?a=1&c=x+y" });
  });

  it("returns undefined on 204", async () => {
    server.use(http.delete(`${API}/thing`, () => new HttpResponse(null, { status: 204 })));
    await expect(apiClient.delete("/thing")).resolves.toBeUndefined();
  });

  it("shapes ErrorBody into ApiError with code, details and Retry-After", async () => {
    server.use(
      http.post(`${API}/login`, () =>
        HttpResponse.json({ code: "rate_limited", message: "x", details: { a: 1 } }, { status: 429, headers: { "Retry-After": "42" } }),
      ),
    );
    const err = await apiClient.post("/login", {}).catch((e: unknown) => e);
    expect(err).toBeInstanceOf(ApiError);
    expect(err).toMatchObject({ status: 429, code: "rate_limited", details: { a: 1 }, retryAfter: 42 });
  });

  it("calls onUnauthorized on 401 for authenticated calls", async () => {
    server.use(http.get(`${API}/me`, () => HttpResponse.json({ code: "http_error", message: "x" }, { status: 401 })));
    await apiClient.get("/me").catch(() => undefined);
    expect(onUnauthorized).toHaveBeenCalledOnce();
  });

  it("maps network failures to code network_error", async () => {
    server.use(http.get(`${API}/down`, () => HttpResponse.error()));
    await expect(apiClient.get("/down")).rejects.toMatchObject({ status: 0, code: "network_error" });
  });

  it("returns ArrayBuffer and headers for binary fields", async () => {
    server.use(
      http.get(`${API}/bin`, () =>
        HttpResponse.arrayBuffer(new Float32Array([1, 2]).buffer, { headers: { "X-Field-Shape": "1,2" } }),
      ),
    );
    const res = await apiClient.binary("/bin");
    expect(new Float32Array(res.data)).toEqual(new Float32Array([1, 2]));
    expect(res.headers.get("X-Field-Shape")).toBe("1,2");
  });
});
