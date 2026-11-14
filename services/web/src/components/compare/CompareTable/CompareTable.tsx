import { flexRender } from "@tanstack/react-table";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCompareTable } from "./CompareTable.hook";
import type { CompareTableProps } from "./CompareTable.types";
import styles from "./CompareTable.module.css";

/** Collapsible table of zone and comfort areas; scrolls inside itself, never the page. */
export function CompareTable(p: CompareTableProps) {
  const { t } = useTranslation();
  const { table, open, toggle } = useCompareTable(p);
  return (
    <section className={styles.root} aria-labelledby="compare-table-title">
      <button type="button" className={styles.head} aria-expanded={open} onClick={toggle}>
        {open ? <ChevronDown aria-hidden size={16} /> : <ChevronUp aria-hidden size={16} />}
        <span id="compare-table-title">{t("compare:table.title")}</span>
      </button>
      {open ? (
        <div className={styles.scroll}>
          <Table>
            <TableHeader>
              {table.getHeaderGroups().map((hg) => (
                <TableRow key={hg.id}>
                  {hg.headers.map((h) => (
                    <TableHead key={h.id} className={h.column.id === "label" ? undefined : styles.num}>
                      {flexRender(h.column.columnDef.header, h.getContext())}
                    </TableHead>
                  ))}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows.map((row) => (
                <TableRow key={row.id}>
                  {row.getVisibleCells().map((c) => (
                    <TableCell key={c.id} className={c.column.id === "label" ? styles.label : styles.num}>
                      {flexRender(c.column.columnDef.cell, c.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
          {p.comfortMissing ? <p className={styles.note}>{t("compare:table.comfortMissing")}</p> : null}
        </div>
      ) : null}
    </section>
  );
}
