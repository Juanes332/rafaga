import type { ColumnDef } from "@tanstack/react-table";
import type { TFunction } from "i18next";
import { formatArea, formatPercentValue } from "@/lib/format/format.number";

export interface AreaCell {
  area_m2: number;
  percent: number;
}

export interface CompareRow {
  label: string;
  acceleration: AreaCell | null;
  stagnation: AreaCell | null;
  reduction: AreaCell | null;
  lawson: Record<string, AreaCell>;
}

export const LAWSON_KEYS = ["A", "B", "C", "D", "E"] as const;

function cell(v: AreaCell | null | undefined): string {
  return v ? `${formatArea(v.area_m2)}  ${formatPercentValue(v.percent)}` : "—";
}

/** Zone and Lawson-class areas per alternative (SCR-18 bottom table). */
export function compareColumns(t: TFunction, withComfort: boolean): ColumnDef<CompareRow>[] {
  const zones: ColumnDef<CompareRow>[] = (["acceleration", "stagnation", "reduction"] as const).map((z) => ({
    id: z,
    header: () => t(`results:zone.${z}`),
    cell: ({ row }) => cell(row.original[z]),
  }));
  const lawson: ColumnDef<CompareRow>[] = withComfort
    ? LAWSON_KEYS.map((k) => ({ id: `lawson-${k}`, header: () => t(`results:lawson.classes.${k}`), cell: ({ row }) => cell(row.original.lawson[k]) }))
    : [];
  return [{ id: "label", header: () => t("compare:table.alternative"), cell: ({ row }) => row.original.label }, ...zones, ...lawson];
}
