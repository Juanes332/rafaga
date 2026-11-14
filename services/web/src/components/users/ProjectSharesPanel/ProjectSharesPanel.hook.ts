import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { projectsQueryOptions } from "@/api/projects/projects.queries";
import { sharesQueryOptions, useToggleShare } from "@/api/shares/shares.queries";
import { usersQueryOptions } from "@/api/users/users.queries";
import { errorMessage } from "@/lib/http/error-copy";
import type { User } from "@/types/auth/auth.types";

/** Pick one of your projects, then switch access per user. */
export function useProjectSharesPanel(selfId: string | undefined) {
  const { t } = useTranslation();
  const [projectId, setProjectId] = useState<string>("");
  const projects = useQuery(projectsQueryOptions());
  const users = useQuery(usersQueryOptions());
  const shares = useQuery({ ...sharesQueryOptions(projectId), enabled: projectId !== "" });
  const toggle = useToggleShare();
  const shared = new Set((shares.data ?? []).map((s) => s.user_id));

  const onToggle = (user: User, grant: boolean) =>
    toggle.mutate(
      { projectId, userId: user.id, grant },
      {
        onSuccess: () => toast(t(grant ? "users:shares.granted" : "users:shares.revoked", { email: user.email })),
        onError: (e) => toast.error(errorMessage(e)),
      },
    );

  return {
    projectId,
    setProjectId,
    projects: (projects.data ?? []).filter((p) => p.role_on_project === "owner"),
    others: (users.data ?? []).filter((u) => u.id !== selfId),
    isShared: (id: string) => shared.has(id),
    loadingShares: shares.isLoading,
    error: shares.error,
    pending: toggle.isPending,
    onToggle,
  };
}
