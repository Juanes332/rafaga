import { useQuery } from "@tanstack/react-query";
import { projectQueryOptions } from "@/api/projects/projects.queries";
import { useSessionStore } from "@/stores/session/session.store";

export interface ProjectAccess {
  /** Reviewers see a read-only UI: launch/edit controls hidden (SCR-22). */
  readOnly: boolean;
  isArchitect: boolean;
}

/** Role on the project plus the account role. */
export function useProjectAccess(projectId: string): ProjectAccess {
  const { data } = useQuery(projectQueryOptions(projectId));
  const role = useSessionStore((s) => s.user?.role);
  const readOnly = data?.role_on_project === "reviewer" || role === "reviewer";
  return { readOnly, isArchitect: role === "architect" };
}
