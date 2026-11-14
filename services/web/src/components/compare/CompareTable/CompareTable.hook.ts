import { useMemo, useState } from "react";
import { getCoreRowModel, useReactTable, type Table } from "@tanstack/react-table";
import { useTranslation } from "react-i18next";
import { compareColumns, type AreaCell, type CompareRow } from "@/tables/compare/compare.columns";
import type { Comfort, ZoneAreas } from "@/types/results/result.types";
import type { CompareTableProps } from "./CompareTable.types";

function zone(z: ZoneAreas | undefined, name: string): AreaCell | null {
  const found = z?.zones.find((x) => x.zone === name);
  return found ? { area_m2: found.area_m2, percent: found.percent } : null;
}

function lawson(c: Comfort | undefined): Record<string, AreaCell> {
  return Object.fromEntries((c?.class_areas ?? []).map((r) => [String(r.class), { area_m2: r.area_m2, percent: r.percent }]));
}

/** Two rows (A, B); reduction only exists for B relative to A. */
export function useCompareTable(p: CompareTableProps): { table: Table<CompareRow>; open: boolean; toggle: () => void } {
  const { t } = useTranslation();
  const [open, setOpen] = useState(true);
  const rows = useMemo((): CompareRow[] => {
    const red = p.areas?.reduction;
    return [
      { label: p.labelA, acceleration: zone(p.areas?.a, "acceleration"), stagnation: zone(p.areas?.a, "stagnation"), reduction: null, lawson: lawson(p.comfort?.a) },
      { label: p.labelB, acceleration: zone(p.areas?.b, "acceleration"), stagnation: zone(p.areas?.b, "stagnation"), reduction: red ? { area_m2: red.area_m2, percent: red.percent } : null, lawson: lawson(p.comfort?.b) },
    ];
  }, [p.areas, p.comfort, p.labelA, p.labelB]);
  const columns = useMemo(() => compareColumns(t, !p.comfortMissing), [t, p.comfortMissing]);
  const table = useReactTable({ data: rows, columns, getCoreRowModel: getCoreRowModel() });
  return { table, open, toggle: () => setOpen((o) => !o) };
}
