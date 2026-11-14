import { ZONE } from "@/engines/fields/zones";
import { patternTile, type ZoneKind } from "@/engines/fields/zone-patterns";
import type { GridView } from "@/engines/fields/grid-view";

const KINDS: Array<[ZoneKind, number]> = [
  ["acceleration", ZONE.acceleration],
  ["stagnation", ZONE.stagnation],
  ["reduction", ZONE.reduction],
];

/** Grid-sized white mask of one zone, north up. */
function maskCanvas(codes: Uint8Array, cols: number, rows: number, code: number): HTMLCanvasElement | null {
  const c = document.createElement("canvas");
  c.width = cols;
  c.height = rows;
  const ctx = c.getContext?.("2d");
  if (!ctx) return null;
  const px = new Uint8ClampedArray(new ArrayBuffer(cols * rows * 4));
  for (let r = 0; r < rows; r += 1) {
    for (let col = 0; col < cols; col += 1) {
      if (codes[r * cols + col] !== code) continue;
      px[((rows - 1 - r) * cols + col) * 4 + 3] = 255;
    }
  }
  ctx.putImageData(new ImageData(px, cols, rows), 0, 0);
  return c;
}

/** Fill at 45 % + pattern in the zone colour, clipped to the zone mask. */
export function drawZones(ctx: CanvasRenderingContext2D, codes: Uint8Array, cols: number, rows: number, view: GridView, colorOf: (k: ZoneKind) => string): void {
  const { width, height } = ctx.canvas;
  for (const [kind, code] of KINDS) {
    const mask = maskCanvas(codes, cols, rows, code);
    const layer = document.createElement("canvas");
    layer.width = width;
    layer.height = height;
    const l = layer.getContext("2d");
    if (!mask || !l) continue;
    l.setTransform(ctx.getTransform());
    l.imageSmoothingEnabled = false;
    l.drawImage(mask, view.ox, view.oy, cols * view.ppc, rows * view.ppc);
    l.globalCompositeOperation = "source-in";
    l.globalAlpha = 0.45;
    l.fillStyle = colorOf(kind);
    l.fillRect(-1e4, -1e4, 2e4, 2e4);
    l.globalAlpha = 1;
    l.globalCompositeOperation = "source-atop";
    const pattern = l.createPattern(patternTile(kind, colorOf(kind)), "repeat");
    if (pattern) {
      l.fillStyle = pattern;
      l.fillRect(-1e4, -1e4, 2e4, 2e4);
    }
    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.drawImage(layer, 0, 0);
    ctx.restore();
  }
}
