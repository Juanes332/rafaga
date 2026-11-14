import type { ColumnDef } from "@tanstack/react-table";
import { Trash2 } from "lucide-react";
import type { TFunction } from "i18next";
import { Button } from "@/components/ui/button";
import { formatRelative } from "@/lib/format/format.date";
import type { Template } from "@/types/settings/settings.types";

export interface TemplateRowActions {
  onApply: (t: Template) => void;
  onDelete: (t: Template) => void;
}

/** Name · created · apply / delete. */
export function templateColumns(t: TFunction, actions: TemplateRowActions): ColumnDef<Template>[] {
  return [
    { accessorKey: "name", header: () => t("templates:columns.name") },
    {
      accessorKey: "created_at",
      header: () => t("templates:columns.created"),
      cell: ({ row }) => (row.original.created_at ? formatRelative(row.original.created_at) : "—"),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">{t("templates:columns.actions")}</span>,
      cell: ({ row }) => (
        <span style={{ display: "inline-flex", gap: "var(--space-1)" }}>
          <Button variant="outline" size="sm" onClick={() => actions.onApply(row.original)}>
            {t("templates:apply.short")}
            <span className="sr-only"> {row.original.name}</span>
          </Button>
          <Button variant="ghost" size="icon" aria-label={t("templates:delete.action", { name: row.original.name })} onClick={() => actions.onDelete(row.original)}>
            <Trash2 aria-hidden />
          </Button>
        </span>
      ),
    },
  ];
}
