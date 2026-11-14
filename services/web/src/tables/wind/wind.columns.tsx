import type { ColumnDef } from "@tanstack/react-table";
import type { TFunction } from "i18next";
import { directionLabel } from "@/lib/format/format.direction";
import { formatNumber, formatPercent } from "@/lib/format/format.number";
import type { WindSector } from "@/types/wind/wind.types";

/** Direction · frequency · p50 · p90 · max (m/s at 10 m). */
export function windSectorColumns(t: TFunction): ColumnDef<WindSector>[] {
  const speed = (key: "p50_ms" | "p90_ms" | "max_ms", label: string): ColumnDef<WindSector> => ({
    accessorKey: key,
    header: () => label,
    cell: ({ row }) => formatNumber(row.original[key], 1),
    meta: { numeric: true },
  });
  return [
    { accessorKey: "center_deg", header: () => t("wind:table.direction"), cell: ({ row }) => directionLabel(row.original.center_deg) },
    {
      accessorKey: "frequency",
      header: () => t("wind:table.frequency"),
      cell: ({ row }) => formatPercent(row.original.frequency),
      meta: { numeric: true },
    },
    speed("p50_ms", t("wind:table.p50")),
    speed("p90_ms", t("wind:table.p90")),
    speed("max_ms", t("wind:table.max")),
  ];
}
