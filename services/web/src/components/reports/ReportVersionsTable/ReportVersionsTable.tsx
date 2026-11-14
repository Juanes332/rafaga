import { flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { reportColumns } from "@/tables/reports/reports.columns";
import type { Report } from "@/types/exports/export.types";
import styles from "./ReportVersionsTable.module.css";

interface ReportVersionsTableProps {
  reports: Report[];
  onDownload: (r: Report) => void;
}

function useReportVersionsTable({ reports, onDownload }: ReportVersionsTableProps) {
  const { t } = useTranslation();
  const columns = useMemo(() => reportColumns(t, onDownload), [t, onDownload]);
  return useReactTable({ data: reports, columns, getCoreRowModel: getCoreRowModel() });
}

/** Report versions, newest first. */
export function ReportVersionsTable(props: ReportVersionsTableProps) {
  const table = useReportVersionsTable(props);
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
