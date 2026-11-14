import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { User } from "@/types/auth/auth.types";
import type { UserCreate } from "@/types/users/user.types";

export const usersKeys = { all: ["users"] as const };

/** Local accounts (architects only). */
export const usersQueryOptions = () =>
  queryOptions({ queryKey: usersKeys.all, queryFn: () => apiClient.get<User[]>("/users") });

/** POST /users. */
export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: UserCreate) => apiClient.post<User>("/users", body),
    onSuccess: () => qc.invalidateQueries({ queryKey: usersKeys.all }),
  });
}

/** DELETE /users/{id}. */
export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiClient.delete(`/users/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: usersKeys.all }),
  });
}
