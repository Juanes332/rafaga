import { queryOptions, useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { Credentials, SetupStatus, Token, User } from "@/types/auth/auth.types";

export const authKeys = {
  setupStatus: ["auth", "setup-status"] as const,
  me: ["auth", "me"] as const,
};

/** First-run gate: needs_setup decides between SCR-01 and SCR-02. */
export const setupStatusQueryOptions = () =>
  queryOptions({
    queryKey: authKeys.setupStatus,
    queryFn: () => apiClient.get<SetupStatus>("/auth/setup-status"),
    staleTime: 0,
  });

export const meQueryOptions = () =>
  queryOptions({ queryKey: authKeys.me, queryFn: () => apiClient.get<User>("/auth/me") });

export const setupAccount = (body: Credentials) => apiClient.post<Token>("/auth/setup", body);
export const login = (body: Credentials) => apiClient.post<Token>("/auth/login", body);

/** POST /auth/setup. */
export function useSetupMutation() {
  return useMutation({ mutationFn: setupAccount });
}

/** POST /auth/login. */
export function useLoginMutation() {
  return useMutation({ mutationFn: login });
}
