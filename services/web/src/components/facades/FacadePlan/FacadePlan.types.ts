import type { EdgeRef } from "@/stores/facades/facades.store";
import type { FacadeElement } from "@/types/facades/facade.types";
import type { Building } from "@/types/geometry/geometry.types";

export interface FacadePlanProps {
  buildings: Building[];
  elements: FacadeElement[];
  selected: EdgeRef | null;
  /** False on the base alternative and for reviewers: edges are not pickable. */
  interactive: boolean;
  onSelect: (edge: EdgeRef) => void;
}
