import type { ColumnDef } from "@tanstack/react-table";
import { Download } from "lucide-react";
import type { TFunction } from "i18next";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/format/format.date";
import { formatPercent } from "@/lib/format/format.number";
import { jobErrorMessage } from "@/lib/http/error-copy";
import type { Report } from "@/types/exports/export.types";

function statusText(t: TFunction, r: Report): string {
  if (r.status === "running") return `${t("reports:status.running")}: ${formatPercent(r.progress ?? 0, 0)}`;
  if (r.status === "failed") return `${t("reports:status.failed")}. ${jobErrorMessage(r.error?.code)}`;
  return t(`reports:status.${r.status}`);
}

/** Version · created · status · download. */
export function reportColumns(t: TFunction, onDownload: (r: Report) => void): ColumnDef<Report>[] {
  return [
    { accessorKey: "version", header: () => t("reports:columns.version"), cell: ({ row }) => t("reports:versionLabel", { version: row.original.version }) },
    {
      accessorKey: "created_at",
      header: () => t("reports:columns.created"),
      cell: ({ row }) => (row.original.created_at ? formatDate(row.original.created_at) : "—"),
    },
    { accessorKey: "status", header: () => t("reports:columns.status"), cell: ({ row }) => statusText(t, row.original) },
    {
      id: "actions",
      header: () => <span className="sr-only">{t("reports:columns.actions")}</span>,
      cell: ({ row }) =>
        row.original.status === "completed" ? (
          <Button variant="outline" size="sm" aria-label={t("reports:downloadVersion", { version: row.original.version })} onClick={() => onDownload(row.original)}>
            <Download aria-hidden />
            {t("reports:download")}
          </Button>
        ) : null,
    },
  ];
}
