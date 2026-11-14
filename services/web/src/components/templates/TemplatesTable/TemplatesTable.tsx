import { flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { templateColumns, type TemplateRowActions } from "@/tables/templates/templates.columns";
import type { Template } from "@/types/settings/settings.types";
import styles from "./TemplatesTable.module.css";

interface TemplatesTableProps extends TemplateRowActions {
  templates: Template[];
}

function useTemplatesTable({ templates, onApply, onDelete }: TemplatesTableProps) {
  const { t } = useTranslation();
  const columns = useMemo(() => templateColumns(t, { onApply, onDelete }), [t, onApply, onDelete]);
  return useReactTable({ data: templates, columns, getCoreRowModel: getCoreRowModel() });
}

/** Saved templates as a list. */
export function TemplatesTable(props: TemplatesTableProps) {
  const table = useTemplatesTable(props);
  return (
    <Table className={styles.table}>
      <TableHeader>
        {table.getHeaderGroups().map((hg) => (
          <TableRow key={hg.id}>
            {hg.headers.map((h) => (
              <TableHead key={h.id}>{flexRender(h.column.columnDef.header, h.getContext())}</TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {table.getRowModel().rows.map((row) => (
          <TableRow key={row.id}>
            {row.getVisibleCells().map((cell) => (
              <TableCell key={cell.id} className={styles[cell.column.id]}>
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
