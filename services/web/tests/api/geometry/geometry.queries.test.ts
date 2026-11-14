import { QueryClient } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  geometryKeys,
  geometryQueryOptions,
  useImportGeometry,
  useSaveGeometry,
  useValidateGeometry,
} from "@/api/geometry/geometry.queries";
import { createQueryWrapper } from "../../utils/render-with-providers";
import { useNodeFormData } from "../../utils/form-data-env";
import { P1, geometryOf, sampleBuildings } from "../../msw/geometry/geometry.handlers";

const P2 = "00000000-0000-4000-8000-0000000000p2";

function setup() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return { client, wrapper: createQueryWrapper(client) };
}

describe("geometry api", () => {
  useNodeFormData();

  it("reads the versioned geometry", async () => {
    const g = await setup().client.fetchQuery(geometryQueryOptions(P1));
    expect(g.version).toBe(3);
    expect(g.buildings).toHaveLength(2);
  });

  it("rejects a stale expected_version with version_conflict", async () => {
    const { wrapper } = setup();
    const { result } = renderHook(() => useSaveGeometry(P1), { wrapper });
    result.current.mutate({ expectedVersion: 1, buildings: sampleBuildings() });
    await waitFor(() => expect(result.current.error).toMatchObject({ status: 409, code: "version_conflict" }));
  });

  it("needs confirm_base_change when alternatives exist, then saves and updates the cache", async () => {
    const { client, wrapper } = setup();
    const spy = vi.spyOn(client, "setQueryData");
    const { result } = renderHook(() => useSaveGeometry(P1), { wrapper });
    result.current.mutate({ expectedVersion: 3, buildings: sampleBuildings() });
    await waitFor(() => expect(result.current.error).toMatchObject({ code: "base_locked" }));
    result.current.mutate({ expectedVersion: 3, buildings: sampleBuildings(), confirmBaseChange: true });
    await waitFor(() => expect(result.current.data?.version).toBe(4));
    expect(spy).toHaveBeenCalledWith(geometryKeys.detail(P1), expect.objectContaining({ version: 4 }));
  });

  it("validates without saving", async () => {
    const { wrapper } = setup();
    const { result } = renderHook(() => useValidateGeometry(P1), { wrapper });
    result.current.mutate([{ ...sampleBuildings()[0], height_m: null }]);
    await waitFor(() => expect(result.current.data?.issues[0].code).toBe("missing_height"));
    expect(geometryOf(P1).version).toBe(3);
  });

  it("imports a file and reports added, missing-height and ignored entities", async () => {
    const { wrapper } = setup();
    const { result } = renderHook(() => useImportGeometry(P2), { wrapper });
    result.current.mutate({ file: new File(["x"], "plano.dxf"), unit: "auto", mode: "append" });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toMatchObject({ buildings_added: 2, detected_unit: "cm" });
    expect(result.current.data?.ignored).toHaveLength(2);
  });

  it("surfaces import_failed with its code", async () => {
    const { wrapper } = setup();
    const { result } = renderHook(() => useImportGeometry(P2), { wrapper });
    result.current.mutate({ file: new File(["x"], "falla.dxf"), unit: "auto", mode: "append" });
    await waitFor(() => expect(result.current.error).toMatchObject({ status: 422, code: "import_failed" }));
  });

  it("refuses imports while alternatives exist (base_locked, no confirm flag)", async () => {
    const { wrapper } = setup();
    const { result } = renderHook(() => useImportGeometry(P1), { wrapper });
    result.current.mutate({ file: new File(["x"], "plano.dxf"), unit: "auto", mode: "append" });
    await waitFor(() => expect(result.current.error).toMatchObject({ status: 409, code: "base_locked" }));
  });
});
