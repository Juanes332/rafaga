import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { usePlaceSearch } from "@/components/location/PlaceSearch/PlaceSearch.hook";
import { geoState } from "../../../msw/geo/geo.handlers";
import { createQueryWrapper } from "../../../utils/render-with-providers";

describe("usePlaceSearch", () => {
  it("searches after the debounce once 3 letters are typed", async () => {
    const { result } = renderHook(() => usePlaceSearch(), { wrapper: createQueryWrapper() });
    act(() => result.current.setText("Pu"));
    expect(result.current.tooShort).toBe(true);
    act(() => result.current.setText("Puerto"));
    await waitFor(() => expect(result.current.results.map((r) => r.name)).toEqual(["Puerto Ficticio"]));
  });

  it("reports an empty result and the offline error", async () => {
    const { result } = renderHook(() => usePlaceSearch(), { wrapper: createQueryWrapper() });
    act(() => result.current.setText("Nada"));
    await waitFor(() => expect(result.current.empty).toBe(true));
    geoState.offline = true;
    act(() => result.current.setText("Villa"));
    await waitFor(() => expect(result.current.error).toMatchObject({ code: "geocoding_unavailable" }));
  });
});
