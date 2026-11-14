/** Placement of a cell grid on a canvas: pixels per cell and the grid's top-left corner. */
export interface GridView {
  ppc: number;
  ox: number;
  oy: number;
  /** Relative to the fitted scale (particles move K × 0.6 px × zoom). */
  zoom: number;
  fitPpc: number;
}

interface PlanGrid {
  origin_x: number;
  origin_y: number;
  dx_m: number;
}

/** Largest square-cell scale that fits, centred. */
export function fitView(cols: number, rows: number, width: number, height: number, pad = 16): GridView {
  const ppc = Math.max(0.01, Math.min((width - 2 * pad) / cols, (height - 2 * pad) / rows));
  return { ppc, ox: (width - cols * ppc) / 2, oy: (height - rows * ppc) / 2, zoom: 1, fitPpc: ppc };
}

/** Screen px → cell units (x east, y north from the south edge). */
export function screenToCell(v: GridView, rows: number, sx: number, sy: number): [number, number] {
  return [(sx - v.ox) / v.ppc, rows - (sy - v.oy) / v.ppc];
}

export function cellToScreen(v: GridView, rows: number, cx: number, cy: number): [number, number] {
  return [v.ox + cx * v.ppc, v.oy + (rows - cy) * v.ppc];
}

export function enuToCell(g: PlanGrid, x: number, y: number): [number, number] {
  return [(x - g.origin_x) / g.dx_m, (y - g.origin_y) / g.dx_m];
}

export function cellToEnu(g: PlanGrid, cx: number, cy: number): [number, number] {
  return [g.origin_x + cx * g.dx_m, g.origin_y + cy * g.dx_m];
}

/** Zoom by `factor` keeping the screen point (sx, sy) fixed; zoom limited to 0.5–12. */
export function zoomAt(v: GridView, factor: number, sx: number, sy: number): GridView {
  const zoom = Math.max(0.5, Math.min(12, v.zoom * factor));
  const ppc = v.fitPpc * zoom;
  const k = ppc / v.ppc;
  return { ...v, zoom, ppc, ox: sx - (sx - v.ox) * k, oy: sy - (sy - v.oy) * k };
}
