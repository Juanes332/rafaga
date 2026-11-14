import { getCoreRowModel, useReactTable, type Table } from "@tanstack/react-table";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { projectColumns } from "@/tables/projects/projects.columns";
import type { ProjectSummary } from "@/types/projects/project.types";
import type { ProjectsTableProps } from "./ProjectsTable.types";

/** Typed TanStack table over project summaries. */
export function useProjectsTable(p: ProjectsTableProps): Table<ProjectSummary> {
  const { t } = useTranslation();
  const { onRename, onDuplicate, onDelete } = p;
  const columns = useMemo(() => projectColumns(t, { onRename, onDuplicate, onDelete }), [t, onRename, onDuplicate, onDelete]);
  return useReactTable({ data: p.projects, columns, getCoreRowModel: getCoreRowModel() });
}
