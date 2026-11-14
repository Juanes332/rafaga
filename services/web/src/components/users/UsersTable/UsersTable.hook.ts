import { getCoreRowModel, useReactTable, type Table } from "@tanstack/react-table";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { userColumns } from "@/tables/users/users.columns";
import type { User } from "@/types/auth/auth.types";

export interface UsersTableProps {
  users: User[];
  selfId: string | undefined;
  onDelete: (u: User) => void;
}

/** Typed TanStack table over local users. */
export function useUsersTable({ users, selfId, onDelete }: UsersTableProps): Table<User> {
  const { t } = useTranslation();
  const columns = useMemo(() => userColumns(t, selfId, onDelete), [t, selfId, onDelete]);
  return useReactTable({ data: users, columns, getCoreRowModel: getCoreRowModel() });
}
