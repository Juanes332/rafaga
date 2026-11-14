import type { EdgeRef } from "@/stores/facades/facades.store";
import type { FacadeElement } from "@/types/facades/facade.types";

export interface FacadeEditorProps {
  projectId: string;
  alternativeId: string;
  edge: EdgeRef;
  buildingName: string;
  /** The strategy already on this edge, if any. */
  element: FacadeElement | null;
  readOnly: boolean;
}

export interface ParamView {
  key: string;
  label: string;
  help: string;
  unit: string;
  min: number;
  max: number;
  defaultValue: number | null;
  value: number | null;
  percent: boolean;
  decimals: number;
}
