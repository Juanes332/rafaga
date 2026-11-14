import type { FacadeStrategy } from "@/types/facades/facade.types";

type Param = FacadeStrategy["parameters"][number];
const p = (key: string, unit: string, min: number, max: number, def: number | null): Param => ({
  key,
  unit,
  min,
  max,
  default: def,
  help_key: `facade.param.${key}`,
});

/** Mirrors the ScreenParams/FinsParams/… ranges and defaults of openapi.yaml. */
export const STRATEGIES: FacadeStrategy[] = [
  { type: "screen", label_key: "facade.screen", help_key: "facade.screen.help", parameters: [p("porosity", "", 0.05, 0.95, 0.4), p("height_m", "m", 0.5, 50, 3), p("offset_m", "m", 0, 5, 0.5)] },
  { type: "fins", label_key: "facade.fins", help_key: "facade.fins.help", parameters: [p("depth_m", "m", 0.1, 3, 0.5), p("pitch_m", "m", 0.3, 10, 1), p("thickness_m", "m", 0.05, 0.5, 0.15), p("height_m", "m", 1, 500, null)] },
  { type: "canopy", label_key: "facade.canopy", help_key: "facade.canopy.help", parameters: [p("overhang_m", "m", 0.5, 6, 2), p("height_m", "m", 2.5, 10, 3.5), p("thickness_m", "m", 0.1, 1, 0.3)] },
  { type: "setback", label_key: "facade.setback", help_key: "facade.setback.help", parameters: [p("setback_m", "m", 0.1, 5, 1), p("floor_height_m", "m", 2.5, 6, 3), p("start_floor", "", 1, 100, 1)] },
  { type: "vegetation", label_key: "facade.vegetation", help_key: "facade.vegetation.help", parameters: [p("lad_m2_m3", "m²/m³", 0.1, 5, 1), p("height_m", "m", 1, 30, 8), p("width_m", "m", 0.5, 5, 3), p("offset_m", "m", 0, 5, 1)] },
];
