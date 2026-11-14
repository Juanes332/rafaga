import { usePlanBackground } from "./PlanBackground.hook";

/** Calibrated trace plan under the buildings (SCR-08). */
export function PlanBackground({ projectId }: { projectId: string }) {
  const layer = usePlanBackground(projectId);
  if (!layer) return null;
  return (
    <image
      href={layer.url}
      x={layer.x}
      y={layer.y}
      width={layer.width}
      height={layer.height}
      opacity={layer.opacity}
      preserveAspectRatio="none"
      style={{ pointerEvents: "none" }}
    />
  );
}
