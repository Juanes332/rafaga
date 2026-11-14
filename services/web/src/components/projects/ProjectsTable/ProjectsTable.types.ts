import type { ProjectRowActions } from "@/tables/projects/projects.columns";
import type { ProjectSummary } from "@/types/projects/project.types";

export interface ProjectsTableProps extends ProjectRowActions {
  projects: ProjectSummary[];
}
