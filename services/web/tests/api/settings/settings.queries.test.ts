import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import { settingsKeys, settingsQueryOptions, useUpdateSettings } from "@/api/settings/settings.queries";
import { createQueryWrapper } from "../../utils/render-with-providers";

describe("settings api", () => {
  it("reads defaults", async () => {
    const s = await new QueryClient().fetchQuery(settingsQueryOptions());
    expect(s.thresholds.k_accel).toBe(1.2);
  });
  it("patches, caches the new settings and invalidates result zones", async () => {
    const client = new QueryClient();
    const spy = vi.spyOn(client, "invalidateQueries");
    const { result } = renderHook(() => useUpdateSettings(), { wrapper: createQueryWrapper(client) });
    result.current.mutate({ vegetation_cd: 0.3 });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(client.getQueryData<{ vegetation_cd: number }>(settingsKeys.detail)?.vegetation_cd).toBe(0.3);
    expect(spy).toHaveBeenCalledWith({ queryKey: ["results"] });
  });
  it("surfaces validation_error", async () => {
    const { result } = renderHook(() => useUpdateSettings(), { wrapper: createQueryWrapper() });
    result.current.mutate({ alternatives_limit: 50 });
    await waitFor(() => expect(result.current.error).toMatchObject({ code: "validation_error" }));
  });
});
