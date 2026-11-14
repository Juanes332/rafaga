import { useMemo, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { fieldQueryOptions } from "@/api/results/results.queries";
import { lutIndex, lutRgb, SPEED_LUT } from "@/engines/colormaps/colormap";
import { fitView } from "@/engines/fields/grid-view";
import { useElementSize } from "@/hooks/media/use-element-size";
import type { Result } from "@/types/results/result.types";
import type { OutputGridSection } from "@/types/simulations/simulation.types";

const M = { left: 52, bottom: 40, top: 12, right: 16 };

function ticks(from: number, to: number, target: number): number[] {
  const span = to - from;
  const step = [5, 10, 20, 25, 50, 100].find((s) => span / s <= target) ?? 200;
  const out: number[] = [];
  for (let v = Math.ceil(from / step) * step; v <= to; v += step) out.push(v);
  return out;
}

/** (s, z) speed field fitted with room for the height and distance axes. */
export function useSectionResult(result: Result) {
  const box = useRef<HTMLDivElement>(null);
  const size = useElementSize(box);
  const grid = result.output_grid as OutputGridSection;
  const speed = useQuery(fieldQueryOptions(result.id, "speed"));
  const max = useMemo(() => {
    let m = 1;
    if (speed.data) for (const v of speed.data.data) if (Number.isFinite(v) && v > m) m = v;
    return Math.ceil(m);
  }, [speed.data]);
  const inner = fitView(grid.ns, grid.nz, Math.max(1, size.width - M.left - M.right), Math.max(1, size.height - M.top - M.bottom), 0);
  const view = { ...inner, ox: M.left, oy: M.top + Math.max(0, size.height - M.top - M.bottom - grid.nz * inner.ppc) };
  const color = useMemo(() => (v: number) => lutRgb(SPEED_LUT, lutIndex(v, [0, max])), [max]);
  const s1 = grid.s0 + grid.ns * grid.dx_m;
  return {
    box,
    size,
    grid,
    field: speed.data,
    error: speed.error,
    view,
    color,
    max,
    zTicks: ticks(0, grid.nz * grid.dx_m, 6).map((z) => ({ v: z, y: view.oy + (grid.nz - z / grid.dx_m) * view.ppc })),
    sTicks: ticks(grid.s0, s1, 8).map((s) => ({ v: s, x: view.ox + ((s - grid.s0) / grid.dx_m) * view.ppc })),
    bottom: view.oy + grid.nz * view.ppc,
  };
}
