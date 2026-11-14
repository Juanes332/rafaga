import { useId } from "react";
import type { ZoneKind } from "@/engines/fields/zone-patterns";

const COLOR: Record<ZoneKind, string> = {
  acceleration: "var(--color-zone-accel)",
  stagnation: "var(--color-zone-stagnation)",
  reduction: "var(--color-zone-reduction)",
};

/** Fill + pattern swatch: the same encoding as the map, readable in greyscale. */
export function ZoneSwatch({ zone }: { zone: ZoneKind }) {
  const id = useId();
  const c = COLOR[zone];
  return (
    <svg width="20" height="14" aria-hidden>
      <defs>
        <pattern id={id} width={zone === "reduction" ? 8 : 6} height={zone === "reduction" ? 8 : 6} patternUnits="userSpaceOnUse">
          {zone === "stagnation" ? <circle cx="1" cy="1" r="0.9" fill={c} /> : null}
          {zone !== "stagnation" ? <path d="M-2,2 l4,-4 M0,8 l8,-8 M6,10 l4,-4" stroke={c} strokeWidth="1.5" /> : null}
          {zone === "reduction" ? <path d="M-2,6 l4,4 M0,0 l8,8 M6,-2 l4,4" stroke={c} strokeWidth="1.5" /> : null}
        </pattern>
      </defs>
      <rect width="20" height="14" rx="2" fill={c} fillOpacity="0.45" />
      <rect width="20" height="14" rx="2" fill={`url(#${id})`} stroke={c} />
    </svg>
  );
}
