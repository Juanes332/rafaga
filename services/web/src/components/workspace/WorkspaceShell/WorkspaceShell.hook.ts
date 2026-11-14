import { useQuery } from "@tanstack/react-query";
import { useParams } from "@tanstack/react-router";
import { projectQueryOptions } from "@/api/projects/projects.queries";
import { useProjectAccess } from "@/hooks/access/use-project-access";

interface UseWorkspaceShell {
  projectId: string;
  projectName: string | undefined;
  readOnly: boolean;
  error: unknown;
}

/** Project context for the shell: name for the breadcrumb, access for the banner. */
export function useWorkspaceShell(): UseWorkspaceShell {
  const { projectId } = useParams({ strict: false }) as { projectId: string };
  const project = useQuery(projectQueryOptions(projectId));
  const { readOnly } = useProjectAccess(projectId);
  return { projectId, projectName: project.data?.name, readOnly, error: project.error };
}
