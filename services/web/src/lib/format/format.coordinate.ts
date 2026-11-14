export type Axis = "lat" | "lon";

/** Degrees, minutes, seconds with the Spanish hemisphere letter (O = oeste). */
export function toDms(value: number | null | undefined, axis: Axis): string {
  if (value == null || !Number.isFinite(value)) return "—";
  // Round once in seconds so 59.6" carries into the minute instead of printing 60".
  const total = Math.round(Math.abs(value) * 3600);
  // A value that rounds to 0″ takes N/E, never "0°00′00″ S".
  const south = value < 0 && total > 0;
  const hemisphere = axis === "lat" ? (south ? "S" : "N") : south ? "O" : "E";
  const deg = Math.floor(total / 3600);
  const min = Math.floor((total % 3600) / 60);
  const sec = total % 60;
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${deg}°${pad(min)}′${pad(sec)}″ ${hemisphere}`;
}
