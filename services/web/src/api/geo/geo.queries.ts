import { queryOptions } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { GeoResult } from "@/types/geo/geo.types";

export const MIN_QUERY = 3;

export const geoKeys = { search: (q: string) => ["geo", "search", q] as const };

/** Place search through the api proxy (Open-Meteo geocoding); disabled under 3 characters. */
export const geoSearchQueryOptions = (q: string) =>
  queryOptions({
    queryKey: geoKeys.search(q),
    // No AbortSignal: jsdom and undici disagree on its class, and results are tiny anyway.
    queryFn: () => apiClient.get<GeoResult[]>("/geo/search", { query: { q } }),
    enabled: q.trim().length >= MIN_QUERY,
    staleTime: 5 * 60_000,
  });
