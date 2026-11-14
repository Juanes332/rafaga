import { describe, expect, it, vi } from "vitest";
import { buildApiBase, loadRuntimeConfig, parseRuntimeConfig } from "@/lib/config/runtime-config";

const loc = { protocol: "http:", hostname: "127.0.0.1" };

describe("parseRuntimeConfig", () => {
  it("accepts a valid port with null override", () => {
    expect(parseRuntimeConfig({ apiPort: 49231, apiBaseUrl: null })).toEqual({ apiPort: 49231, apiBaseUrl: null });
  });
  it("rejects port 0, which compose writes before ports are discovered", () => {
    expect(parseRuntimeConfig({ apiPort: 0, apiBaseUrl: null })).toBeNull();
  });
  it("rejects non-objects and wrong types", () => {
    expect(parseRuntimeConfig("x")).toBeNull();
    expect(parseRuntimeConfig({ apiPort: "80" })).toBeNull();
  });
  it("accepts an override even without a port", () => {
    expect(parseRuntimeConfig({ apiBaseUrl: "http://10.0.0.2:8000" })).toEqual({ apiPort: null, apiBaseUrl: "http://10.0.0.2:8000" });
  });
});

describe("buildApiBase", () => {
  it("uses the page hostname so localhost and 127.0.0.1 both work", () => {
    expect(buildApiBase({ apiPort: 49231, apiBaseUrl: null }, loc)).toBe("http://127.0.0.1:49231/api/v1");
    expect(buildApiBase({ apiPort: 5, apiBaseUrl: null }, { protocol: "http:", hostname: "localhost" })).toBe("http://localhost:5/api/v1");
  });
  it("prefers apiBaseUrl and strips a trailing slash", () => {
    expect(buildApiBase({ apiPort: 1, apiBaseUrl: "http://h:8000/" }, loc)).toBe("http://h:8000/api/v1");
  });
});

describe("loadRuntimeConfig", () => {
  it("fetches /config.json with no-store and returns the base", async () => {
    const fetchFn = vi.fn().mockResolvedValue(new Response(JSON.stringify({ apiPort: 7, apiBaseUrl: null })));
    await expect(loadRuntimeConfig(fetchFn, loc)).resolves.toBe("http://127.0.0.1:7/api/v1");
    expect(fetchFn).toHaveBeenCalledWith("/config.json", { cache: "no-store" });
  });
  it("returns null when the file is missing or invalid", async () => {
    const missing = vi.fn().mockResolvedValue(new Response("nope", { status: 404 }));
    await expect(loadRuntimeConfig(missing, loc)).resolves.toBeNull();
    const broken = vi.fn().mockResolvedValue(new Response("{not json"));
    await expect(loadRuntimeConfig(broken, loc)).resolves.toBeNull();
    const down = vi.fn().mockRejectedValue(new TypeError("network"));
    await expect(loadRuntimeConfig(down, loc)).resolves.toBeNull();
  });
});
