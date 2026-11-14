import { describe, expect, it } from "vitest";
import { ApiError } from "@/lib/http/api-error";
import { errorMessage } from "@/lib/http/error-copy";

describe("errorMessage", () => {
  it("maps a known code to cause + fix copy", () => {
    expect(errorMessage(new ApiError(409, "location_missing", "x"))).toMatch(/^Fija la ubicación del proyecto/);
  });
  it("includes Retry-After seconds for rate limits", () => {
    expect(errorMessage(new ApiError(429, "rate_limited", "x", {}, 37))).toContain("37 s");
  });
  it("proposes the coarser cell for mesh_too_large", () => {
    expect(errorMessage(new ApiError(422, "mesh_too_large", "x", { proposed_dx_m: 1.5 }))).toContain("1,5 m");
  });
  it("falls back to generic copy for unknown codes and non-API errors", () => {
    expect(errorMessage(new ApiError(500, "weird", "x"))).toMatch(/^Algo falló/);
    expect(errorMessage(new Error("boom"))).toMatch(/^Algo falló/);
  });
  it("never shows the English server message", () => {
    expect(errorMessage(new ApiError(500, "weird", "database exploded"))).not.toContain("database");
  });
});
