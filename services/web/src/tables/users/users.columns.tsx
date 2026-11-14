import type { ColumnDef } from "@tanstack/react-table";
import { Trash2 } from "lucide-react";
import type { TFunction } from "i18next";
import { Button } from "@/components/ui/button";
import { formatRelative } from "@/lib/format/format.date";
import type { User } from "@/types/auth/auth.types";

/** Email · role · created · delete (never offered for yourself). */
export function userColumns(t: TFunction, selfId: string | undefined, onDelete: (u: User) => void): ColumnDef<User>[] {
  return [
    {
      accessorKey: "email",
      header: () => t("users:columns.email"),
      cell: ({ row }) => (row.original.id === selfId ? t("users:you", { email: row.original.email }) : row.original.email),
    },
    { accessorKey: "role", header: () => t("users:columns.role"), cell: ({ row }) => t(`users:roles.${row.original.role}`) },
    {
      accessorKey: "created_at",
      header: () => t("users:columns.created"),
      cell: ({ row }) => (row.original.created_at ? formatRelative(row.original.created_at) : "—"),
    },
    {
      id: "actions",
      header: () => <span className="sr-only">{t("users:columns.actions")}</span>,
      cell: ({ row }) =>
        row.original.id === selfId ? null : (
          <Button variant="ghost" size="icon" aria-label={t("users:delete.action", { email: row.original.email })} onClick={() => onDelete(row.original)}>
            <Trash2 aria-hidden />
          </Button>
        ),
    },
  ];
}
