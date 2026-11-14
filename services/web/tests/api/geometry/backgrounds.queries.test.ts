import { QueryClient } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  BACKGROUND_MAX_BYTES,
  backgroundPageQueryOptions,
  backgroundsQueryOptions,
  useUpdateBackground,
  useUploadBackground,
} from "@/api/geometry/backgrounds.queries";
import { createQueryWrapper } from "../../utils/render-with-providers";
import { useNodeFormData } from "../../utils/form-data-env";
import { P1 } from "../../msw/geometry/geometry.handlers";

function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return { client, wrapper: createQueryWrapper(client) };
}

describe("backgrounds api", () => {
  useNodeFormData();

  it("caps uploads at 25 MB", () => {
    expect(BACKGROUND_MAX_BYTES).toBe(25 * 1024 * 1024);
  });

  it("uploads a PDF, reports its pages and calibrates it", async () => {
    const { client, wrapper } = setup();
    const up = renderHook(() => useUploadBackground(P1), { wrapper });
    up.result.current.mutate(new File(["%PDF"], "plano.pdf"));
    await waitFor(() => expect(up.result.current.data?.page_count).toBe(3));
    const id = up.result.current.data?.id as string;
    const upd = renderHook(() => useUpdateBackground(P1), { wrapper });
    upd.result.current.mutate({ id, patch: { calibration: { p1: [0, 0], p2: [100, 0], distance_m: 20 } } });
    await waitFor(() => expect(upd.result.current.data?.metres_per_pixel).toBeCloseTo(0.2));
    const list = await client.fetchQuery(backgroundsQueryOptions(P1));
    expect(list).toHaveLength(1);
  });

  it("fetches a page as a blob URL", async () => {
    const url = await setup().client.fetchQuery(backgroundPageQueryOptions("bg", 1));
    expect(url).toMatch(/^blob:/);
  });

  it("rejects unsupported formats", async () => {
    const { wrapper } = setup();
    const up = renderHook(() => useUploadBackground(P1), { wrapper });
    up.result.current.mutate(new File(["x"], "plano.dwg"));
    await waitFor(() => expect(up.result.current.error).toMatchObject({ code: "unsupported_format" }));
  });
});
