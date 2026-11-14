const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MIN = 60_000;
const HOUR = 60 * MIN;

/** "12 nov 2026" in local time. */
export function formatDate(iso: string): string {
  const d = new Date(iso);
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

/** Relative under 48 h ("hace 2 h", "ayer"), absolute beyond. */
export function formatRelative(iso: string, now: Date = new Date()): string {
  const diff = now.getTime() - new Date(iso).getTime();
  if (diff < MIN) return "hace un momento";
  if (diff < HOUR) return `hace ${Math.floor(diff / MIN)} min`;
  if (diff < 24 * HOUR) return `hace ${Math.floor(diff / HOUR)} h`;
  if (diff < 48 * HOUR) return "ayer";
  return formatDate(iso);
}

/** ETA seconds → "3 min 5 s". */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null || !Number.isFinite(seconds)) return "—";
  const s = Math.max(0, Math.round(seconds));
  if (s < 60) return `${s} s`;
  if (s < 3600) return `${Math.floor(s / 60)} min ${s % 60} s`;
  return `${Math.floor(s / 3600)} h ${Math.floor((s % 3600) / 60)} min`;
}
