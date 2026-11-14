import { flexRender } from "@tanstack/react-table";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useProjectsTable } from "./ProjectsTable.hook";
import type { ProjectsTableProps } from "./ProjectsTable.types";
import styles from "./ProjectsTable.module.css";

/** List, not a card grid: what the architect scans is name, location, date. */
export function ProjectsTable(props: ProjectsTableProps) {
  const table = useProjectsTable(props);
  return (
    <Table className={styles.table}>
      <TableHeader>
        {table.getHeaderGroups().map((hg) => (
          <TableRow key={hg.id}>
            {hg.headers.map((h) => (
              <TableHead key={h.id} className={styles[h.column.id]}>
                {flexRender(h.column.columnDef.header, h.getContext())}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {table.getRowModel().rows.map((row) => (
          <TableRow key={row.id} className={styles.row}>
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
