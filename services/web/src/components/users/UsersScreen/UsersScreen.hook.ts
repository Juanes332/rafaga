import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { useDeleteUser, usersQueryOptions } from "@/api/users/users.queries";
import { useSessionStore } from "@/stores/session/session.store";
import type { User } from "@/types/auth/auth.types";

/** SCR-22: architects manage accounts; reviewers get an explanation and no request is made. */
export function useUsersScreen() {
  const { t } = useTranslation();
  const self = useSessionStore((s) => s.user);
  const isArchitect = self?.role === "architect";
  const users = useQuery({ ...usersQueryOptions(), enabled: isArchitect });
  const remove = useDeleteUser();
  const [deleting, setDeleting] = useState<User | null>(null);

  const onConfirmDelete = () =>
    deleting &&
    remove.mutate(deleting.id, { onSuccess: () => toast(t("users:delete.done")), onSettled: () => setDeleting(null) });

  return {
    isArchitect,
    selfId: self?.id,
    users: users.data ?? [],
    loadError: users.error,
    deleteError: remove.error,
    deleting,
    onDelete: useCallback((u: User) => setDeleting(u), []),
    onCancelDelete: () => setDeleting(null),
    onConfirmDelete,
  };
}
