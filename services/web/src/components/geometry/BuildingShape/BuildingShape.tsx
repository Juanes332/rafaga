import { memo } from "react";
import { centroid } from "@/engines/geometry/polygon";
import { toSvgPoints } from "@/components/geometry/PlanCanvas/PlanCanvas.utils";
import { cn } from "@/lib/utils";
import type { BuildingShapeProps } from "./BuildingShape.types";
import styles from "./BuildingShape.module.css";

/** One focusable block; memoised so a drag only re-renders the dragged shape. */
export const BuildingShape = memo(function BuildingShape(p: BuildingShapeProps) {
  const [cx, cy] = centroid(p.building.footprint);
  const transform = p.offset ? `translate(${p.offset[0]} ${-p.offset[1]})` : undefined;
  return (
    <g
      className={cn(styles.root, p.selected && styles.selected, p.building.missing_height && styles.missing)}
      transform={transform}
      tabIndex={p.interactive ? 0 : -1}
      role="button"
      aria-pressed={p.selected}
      data-building-id={p.building.id}
      onPointerDown={(e) => p.onPointerDown(p.building.id, e)}
      onKeyDown={(e) => p.onKeyDown(p.building.id, e)}
    >
      <polygon className={styles.shape} points={toSvgPoints(p.building.footprint)} vectorEffect="non-scaling-stroke" />
      <text className={styles.label} x={cx} y={-cy - p.fontSize * 0.6} fontSize={p.fontSize} textAnchor="middle" dominantBaseline="middle">
        {p.building.name}
      </text>
      <text className={styles.height} x={cx} y={-cy + p.fontSize * 0.7} fontSize={p.fontSize * 0.92} textAnchor="middle" dominantBaseline="middle">
        {` ${p.heightText}`}
      </text>
    </g>
  );
});
