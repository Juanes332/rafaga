import type { Axis } from "@/lib/format/format.coordinate";

export interface LatLon {
  lat: number;
  lon: number;
}

const NUM = "\\d+(?:[.,]\\d+)?";
// [hemisphere] [-]deg[°] [min['] [sec["]] [hemisphere]; a mark or a space must separate
// the parts, so run-together digits (5°3213") are rejected instead of guessed.
const AXIS_RE = new RegExp(
  `^([NSEWO])?\\s*(-)?\\s*(${NUM})(?:\\s*°)?(?:(?:(?<=°)\\s*|\\s+)(${NUM})(?:\\s*')?(?:(?:(?<=')\\s*|\\s+)(${NUM})(?:\\s*")?)?)?\\s*([NSEWO])?$`,
  "i",
);
const SOUTH_WEST = new Set(["S", "W", "O"]);
const ALLOWED: Record<Axis, string> = { lat: "NS", lon: "EWO" };

function num(text: string | undefined): number {
  return text === undefined ? 0 : Number(text.replace(",", "."));
}

/** Unify typographic primes and degree look-alikes before matching. */
function normalize(text: string): string {
  return text
    .trim()
    .replace(/[′’‘`´]{2}|″|”|“/g, '"')
    .replace(/[′’‘`´]/g, "'")
    .replace(/[º˚]/g, "°")
    .replace(/\s+/g, " ");
}

/** Decimal, DDM or DMS with N/S/E/W/O letters (comma or dot decimals) → signed degrees. */
export function parseAxis(text: string, axis: Axis): number | null {
  const m = AXIS_RE.exec(normalize(text).replace(/''/g, '"'));
  if (!m) return null;
  const [, pre, minus, deg, min, sec, post] = m;
  if (pre && post) return null;
  const hemi = (pre ?? post)?.toUpperCase();
  if (hemi && !ALLOWED[axis].includes(hemi)) return null;
  if (hemi && minus) return null;
  if (min !== undefined && /[.,]/.test(deg)) return null;
  if (sec !== undefined && /[.,]/.test(min ?? "")) return null;
  if (num(min) >= 60 || num(sec) >= 60) return null;
  const abs = num(deg) + num(min) / 60 + num(sec) / 3600;
  return minus || (hemi && SOUTH_WEST.has(hemi)) ? -abs : abs;
}

function inRange({ lat, lon }: LatLon): boolean {
  return Math.abs(lat) <= 90 && Math.abs(lon) <= 180;
}

/** Parse the two typed fields (any supported notation) and check WGS84 ranges. */
export function parseCoords(latText: string, lonText: string): LatLon | null {
  const lat = parseAxis(latText, "lat");
  const lon = parseAxis(lonText, "lon");
  if (lat === null || lon === null) return null;
  const c = { lat, lon };
  return inRange(c) ? c : null;
}

function splitPair(text: string): [string, string] | null {
  const t = normalize(text);
  if (t.includes(";")) {
    const [a, b, ...rest] = t.split(";");
    return b !== undefined && rest.length === 0 ? [a, b] : null;
  }
  // Leading hemisphere letters start each coordinate: `N 5 32 O 73 21`, `S4.5, W74.25`.
  const byLeading = /^([NSEWO][^A-Za-z]*?)\s*,?\s*([NSEWO][^A-Za-z]*)$/i.exec(t);
  if (byLeading) return [byLeading[1], byLeading[2]];
  // Hemisphere letters end the first coordinate: `5 32 N 73 21 W`, `73 W, 5 N`.
  const byLetter = /^(.*?[NSEWO])\s*,?\s*((?:[NSEWO]\s*)?\d.*)$/i.exec(t);
  if (byLetter && /[A-Za-z]/.test(byLetter[2])) return [byLetter[1], byLetter[2]];
  // Dot decimals leave the comma free as a separator: `4.60976,-74.08175`.
  const byBareComma = /^(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)$/.exec(t);
  if (byBareComma) return [byBareComma[1], byBareComma[2]];
  const byComma = /^(.+?),\s+(.+)$/.exec(t);
  if (byComma) return [byComma[1], byComma[2]];
  const bySpace = /^(-?\d+(?:[.,]\d+)?)\s+(-?\d+(?:[.,]\d+)?)$/.exec(t);
  return bySpace ? [bySpace[1], bySpace[2]] : null;
}

/** A whole pasted position in one string; the hemisphere letters decide which is which. */
export function parseCoordPair(text: string): LatLon | null {
  const parts = splitPair(text);
  if (!parts) return null;
  const direct = parseCoords(parts[0], parts[1]);
  return direct ?? parseCoords(parts[1], parts[0]);
}
