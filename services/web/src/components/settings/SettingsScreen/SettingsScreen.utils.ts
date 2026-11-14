import { isApiError } from "@/lib/http/api-error";
import type { Settings, SettingsPatch } from "@/types/settings/settings.types";

export type Path = Array<string | number>;

/** Immutable set at a path; arrays stay arrays. */
export function withPath<T>(obj: T, path: Path, value: unknown): T {
  if (path.length === 0) return value as T;
  const [head, ...rest] = path;
  const src = obj as unknown as Record<string | number, unknown>;
  const copy = (Array.isArray(obj) ? [...obj] : { ...src }) as Record<string | number, unknown>;
  copy[head] = withPath(src[head], rest, value);
  return copy as unknown as T;
}

function increasing(values: Array<number | null>): boolean {
  const nums = values.filter((v): v is number => v !== null);
  return nums.every((v, i) => i === 0 || v > nums[i - 1]);
}

/** Cross-field rules the single-field ranges cannot express. */
export function orderErrors(s: Settings): { zones: boolean; lawson: boolean } {
  return {
    zones: s.thresholds.k_stagnation >= s.thresholds.k_accel,
    lawson:
      !increasing(s.lawson.comfort.map((c) => c.threshold_ms)) || !increasing(s.lawson.safety.map((c) => c.threshold_ms)),
  };
}

/** 422 bodies list locations only (no message); map each to a dotted field path. */
export function serverFieldErrors(error: unknown): string[] {
  if (!isApiError(error)) return [];
  const list = error.details.errors;
  if (!Array.isArray(list)) return [];
  return list
    .map((e) => (Array.isArray((e as { loc?: unknown }).loc) ? ((e as { loc: unknown[] }).loc.map(String)) : []))
    .map((loc) => (loc[0] === "body" ? loc.slice(1) : loc).join("."))
    .filter(Boolean);
}

export function toPatch(s: Settings): SettingsPatch {
  return {
    thresholds: s.thresholds,
    lawson: s.lawson,
    turbulence_intensity_default: s.turbulence_intensity_default,
    vegetation_cd: s.vegetation_cd,
    alternatives_limit: s.alternatives_limit,
  };
}
