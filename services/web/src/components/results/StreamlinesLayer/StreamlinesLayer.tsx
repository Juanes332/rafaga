import { useMemo } from "react";
import { cellToScreen, type GridView } from "@/engines/fields/grid-view";

interface StreamlinesLayerProps {
  lines: number[][];
  rows: number;
  view: GridView;
  width: number;
  height: number;
  className?: string;
}

/** Static streamlines (1 px, ink 60 %): the reduced-motion and no-WebGL2 fallback. */
export function StreamlinesLayer({ lines, rows, view, width, height, className }: StreamlinesLayerProps) {
  const paths = useMemo(
    () =>
      lines.map((l) => {
        const pts: string[] = [];
        for (let i = 0; i < l.length; i += 2) {
          const [x, y] = cellToScreen(view, rows, l[i], l[i + 1]);
          pts.push(`${x.toFixed(1)},${y.toFixed(1)}`);
        }
        return `M${pts.join("L")}`;
      }),
    [lines, rows, view],
  );
  return (
    <svg className={className} width={width} height={height} aria-hidden data-testid="streamlines">
      {paths.map((d, i) => (
        <path key={i} d={d} fill="none" stroke="var(--color-ink)" strokeOpacity={0.6} strokeWidth={1} />
      ))}
    </svg>
  );
}
