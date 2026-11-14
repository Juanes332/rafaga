import { QueryClient } from "@tanstack/react-query";
import { isApiError } from "@/lib/http/api-error";

/** Single application-wide QueryClient. */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // 4xx answers are facts, not glitches: never retry them.
      retry: (count, error) => count < 2 && !(isApiError(error) && error.status >= 400 && error.status < 500),
    },
    mutations: { retry: false },
  },
});
