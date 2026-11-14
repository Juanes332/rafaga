/** The subset of the canonical scene (scene.schema.json) the viewers read; the generated type is unusable here. */
export interface ScenePrism {
  id: string;
  origin: { kind: string; building_id: string | null; element_id: string | null };
  footprint: number[][];
  holes?: number[][][];
  z_min: number;
  z_max: number;
}

export interface ScenePorous extends ScenePrism {
  model: "screen" | "vegetation";
}

export interface SceneView {
  schema_version: "1.0";
  h_max_m: number;
  analysis_height_m: number;
  solids: ScenePrism[];
  porous: ScenePorous[];
  warnings: Array<{ code: string; ref: string }>;
}
