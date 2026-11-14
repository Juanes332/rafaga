import { queryOptions } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { SystemStatus } from "@/types/system/system.types";

export const systemKeys = { status: ["system", "status"] as const };

/** Compute device and service health for the top bar; refreshed every 15 s. */
export const systemStatusQueryOptions = () =>
  queryOptions({
    queryKey: systemKeys.status,
    queryFn: () => apiClient.get<SystemStatus>("/system/status"),
    refetchInterval: 15_000,
  });
