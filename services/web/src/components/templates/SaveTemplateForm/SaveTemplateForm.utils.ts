import { facadeDefaultsFrom } from "@/api/templates/templates.queries";
import type { FacadeStrategy } from "@/types/facades/facade.types";
import type { Settings, TemplatePayload } from "@/types/settings/settings.types";
import type { WindClimate } from "@/types/wind/wind.types";

// Used when the source project has no wind yet: the BR-08 "urban" category.
export const FALLBACK_TERRAIN = { terrain_category: "urban", z0_m: 1.0 } as const;

/** Template payload from the current settings and one project's terrain; never any location key. */
export function buildPayload(settings: Settings, wind: WindClimate | null | undefined, strategies: FacadeStrategy[]): TemplatePayload {
  return {
    terrain_category: wind?.terrain_category ?? FALLBACK_TERRAIN.terrain_category,
    z0_m: wind?.z0_m ?? FALLBACK_TERRAIN.z0_m,
    thresholds: settings.thresholds,
    lawson: settings.lawson,
    // The generated type models the open object as Record<string, never>; the contract allows any keys.
    facade_defaults: facadeDefaultsFrom(strategies) as unknown as TemplatePayload["facade_defaults"],
  };
}
