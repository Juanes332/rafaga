import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { geoSearchQueryOptions, MIN_QUERY } from "@/api/geo/geo.queries";
import type { GeoResult } from "@/types/geo/geo.types";

interface UsePlaceSearch {
  text: string;
  setText: (v: string) => void;
  results: GeoResult[];
  searching: boolean;
  tooShort: boolean;
  empty: boolean;
  error: unknown;
}

const DEBOUNCE_MS = 300;

/** Debounced place search; results come from the api's geocoding proxy. */
export function usePlaceSearch(): UsePlaceSearch {
  const [text, setText] = useState("");
  const [query, setQuery] = useState("");
  useEffect(() => {
    const id = window.setTimeout(() => setQuery(text.trim()), DEBOUNCE_MS);
    return () => window.clearTimeout(id);
  }, [text]);
  const search = useQuery(geoSearchQueryOptions(query));
  const tooShort = text.trim().length > 0 && text.trim().length < MIN_QUERY;
  return {
    text,
    setText,
    results: search.data ?? [],
    searching: search.isFetching,
    tooShort,
    empty: search.isSuccess && (search.data?.length ?? 0) === 0,
    error: search.error,
  };
}
