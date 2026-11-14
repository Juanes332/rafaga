import type { components } from "@/types/api/openapi.gen";

type S = components["schemas"];

export type ScreenParams = S["ScreenParams"];
export type FinsParams = S["FinsParams"];
export type CanopyParams = S["CanopyParams"];
export type SetbackParams = S["SetbackParams"];
export type VegetationParams = S["VegetationParams"];
export type Adjustment = S["Adjustment"];
export type FacadeStrategy = S["FacadeStrategy"];
export type FacadeElementPatch = S["FacadeElementPatch"];
export type StrategyType = FacadeStrategy["type"];
export type FacadeElementTyped = S["FacadeElementTyped"];

// openapi-typescript mangles allOf + discriminator here, so these mirror the YAML by hand.
export type FacadeElement = {
  id: string;
  building_id: string;
  edge_index: number;
  orphaned?: boolean;
} & FacadeElementTyped;

export type FacadeElementWithAdjustments = FacadeElement & { adjustments: Adjustment[] };

export interface FacadeElementCreate {
  building_id: string;
  edge_index: number;
  type: StrategyType;
  params: Record<string, number | null>;
}
