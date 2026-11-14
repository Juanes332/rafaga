import { queryOptions } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import { decodeField, type Field } from "@/engines/fields/field.decode";
import type { Result, Viewer3D, ZoneAreas } from "@/types/results/result.types";

export type FieldName = "K" | "ux" | "uy" | "uz" | "us" | "speed" | "mask" | "ti" | "slice_xz" | "slice_yz" | "lawson_class" | "exceedance";

export const resultsKeys = {
  detail: (id: string) => ["results", id] as const,
  field: (id: string, name: FieldName) => ["results", id, "field", name] as const,
  zones: (id: string, kAccel: number, kStag: number) => ["results", id, "zones", kAccel, kStag] as const,
};

/** Result metadata: grid, stats, available fields. Immutable once written. */
export const resultQueryOptions = (id: string) =>
  queryOptions({
    queryKey: resultsKeys.detail(id),
    queryFn: () => apiClient.get<Result>(`/results/${id}`),
    staleTime: Infinity,
  });

/** Binary field decoded to a typed array; fetched with the bearer token, never via URL. */
export const fieldQueryOptions = (id: string, name: FieldName) =>
  queryOptions({
    queryKey: resultsKeys.field(id, name),
    queryFn: async (): Promise<Field> => {
      const res = await apiClient.binary(`/results/${id}/fields/${name}`);
      return decodeField(res.data, res.headers);
    },
    staleTime: Infinity,
  });

/** Zone areas re-thresholded server-side for the current settings. */
export const zonesQueryOptions = (id: string, kAccel: number, kStagnation: number) =>
  queryOptions({
    queryKey: resultsKeys.zones(id, kAccel, kStagnation),
    queryFn: () =>
      apiClient.get<ZoneAreas>(`/results/${id}/zones`, { query: { k_accel: kAccel, k_stagnation: kStagnation } }),
  });

/** Buildings, slices and streamlines for volume3d results (SCR-16). */
export const viewer3dQueryOptions = (id: string) =>
  queryOptions({
    queryKey: ["results", id, "viewer3d"] as const,
    queryFn: () => apiClient.get<Viewer3D>(`/results/${id}/viewer3d`),
    staleTime: Infinity,
  });
