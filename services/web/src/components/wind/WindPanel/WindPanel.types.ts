import type { UseWindStep } from "@/components/wind/WindStep/WindStep.hook";

export type WindPanelProps = Pick<
  UseWindStep,
  "wind" | "terrain" | "readOnly" | "manual" | "fetching" | "onFetch" | "onManual" | "onPatch" | "density" | "elevation" | "patchError"
>;
