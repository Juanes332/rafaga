import type { ZoneKind } from "@/engines/fields/zone-patterns";

export interface ZoneLegendItem {
  zone: ZoneKind;
  area_m2: number;
  percent: number;
}

export interface ZoneLegendProps {
  items: ZoneLegendItem[];
  className?: string;
}
