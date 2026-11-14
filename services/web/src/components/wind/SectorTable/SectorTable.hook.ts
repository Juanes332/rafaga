import { getCoreRowModel, useReactTable, type Table } from "@tanstack/react-table";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { windSectorColumns } from "@/tables/wind/wind.columns";
import type { WindSector } from "@/types/wind/wind.types";

/** Typed table over the 16 sectors. */
export function useSectorTable(sectors: WindSector[]): Table<WindSector> {
  const { t } = useTranslation();
  const columns = useMemo(() => windSectorColumns(t), [t]);
  return useReactTable({ data: sectors, columns, getCoreRowModel: getCoreRowModel() });
}
