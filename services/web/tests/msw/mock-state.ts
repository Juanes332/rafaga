/** Each domain registers a reset so mutable mock state never leaks between tests. */
const resets: Array<() => void> = [];

export function registerReset(fn: () => void): void {
  resets.push(fn);
  fn();
}

export function resetMockState(): void {
  for (const fn of resets) fn();
}

let seq = 0;
/** Deterministic uuid-shaped ids for fixtures. */
export function mockId(prefix = "0"): string {
  seq += 1;
  const tail = `${prefix}${seq.toString(16)}`.padStart(12, "0").slice(-12);
  return `00000000-0000-4000-8000-${tail}`;
}

export function errorBody(code: string, message = code, details: Record<string, unknown> = {}) {
  return { code, message, details };
}
