import type { ColumnDef } from "@tanstack/react-table";
import { Link } from "@tanstack/react-router";
import { MoreHorizontal } from "lucide-react";
import type { TFunction } from "i18next";
import { Button } from "@/components/ui/button";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuSeparator, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { formatRelative } from "@/lib/format/format.date";
import type { ProjectSummary } from "@/types/projects/project.types";

export interface ProjectRowActions {
  onRename: (p: ProjectSummary) => void;
  onDuplicate: (p: ProjectSummary) => void;
  onDelete: (p: ProjectSummary) => void;
}

/** Name · location state · last update · ⋯ menu. */
export function projectColumns(t: TFunction, actions: ProjectRowActions): ColumnDef<ProjectSummary>[] {
  return [
    {
      accessorKey: "name",
      header: () => t("projects:columns.name"),
      cell: ({ row }) => (
        <Link to="/projects/$projectId" params={{ projectId: row.original.id }} data-row-link>
          {row.original.name}
        </Link>
      ),
    },
    {
      accessorKey: "has_location",
      header: () => t("projects:columns.location"),
      cell: ({ row }) => (row.original.has_location ? t("projects:hasLocation") : t("projects:noLocation")),
    },
    {
      accessorKey: "updated_at",
      header: () => t("projects:columns.updated"),
      cell: ({ row }) => formatRelative(row.original.updated_at),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">{t("projects:columns.actions")}</span>,
      cell: ({ row }) => {
        const p = row.original;
        const owner = p.role_on_project === "owner";
        return (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" aria-label={`${t("common:moreActions")}: ${p.name}`}>
                <MoreHorizontal aria-hidden />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              {owner ? <DropdownMenuItem onSelect={() => actions.onRename(p)}>{t("projects:actions.rename")}</DropdownMenuItem> : null}
              <DropdownMenuItem onSelect={() => actions.onDuplicate(p)}>{t("projects:actions.duplicate")}</DropdownMenuItem>
              {owner ? <DropdownMenuSeparator /> : null}
              {owner ? (
                <DropdownMenuItem destructive onSelect={() => actions.onDelete(p)}>
                  {t("projects:actions.delete")}
                </DropdownMenuItem>
              ) : null}
            </DropdownMenuContent>
          </DropdownMenu>
        );
      },
    },
  ];
}
