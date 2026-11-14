import { flexRender } from "@tanstack/react-table";
import { useTranslation } from "react-i18next";
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { WindSector } from "@/types/wind/wind.types";
import { useSectorTable } from "./SectorTable.hook";
import styles from "./SectorTable.module.css";

function isNumeric(meta: unknown): boolean {
  return typeof meta === "object" && meta !== null && "numeric" in meta;
}

/** Frequency and p50/p90/max per direction; figures right-aligned and tabular. */
export function SectorTable({ sectors }: { sectors: WindSector[] }) {
  const { t } = useTranslation();
  const table = useSectorTable(sectors);
  return (
    <Table className={styles.table}>
      <TableCaption>{t("wind:table.caption")}</TableCaption>
      <TableHeader>
        {table.getHeaderGroups().map((hg) => (
          <TableRow key={hg.id}>
            {hg.headers.map((h) => (
              <TableHead key={h.id} className={isNumeric(h.column.columnDef.meta) ? styles.num : undefined}>
                {flexRender(h.column.columnDef.header, h.getContext())}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {table.getRowModel().rows.map((row) => (
          <TableRow key={row.id}>
            {row.getVisibleCells().map((cell) => (
              <TableCell key={cell.id} className={isNumeric(cell.column.columnDef.meta) ? styles.num : undefined}>
                {flexRender(cell.column.columnDef.cell, cell.getContext())}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
