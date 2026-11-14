import { rectFromCorners, type Point } from "@/engines/geometry/polygon";
import { toSvgPoints } from "@/components/geometry/PlanCanvas/PlanCanvas.utils";
import type { Gesture } from "@/components/geometry/PlanCanvas/PlanCanvas.types";
import styles from "./PlanPreview.module.css";

interface PlanPreviewProps {
  gesture: Gesture;
  polygon: Point[];
  hover: Point | null;
  ruler: Point[];
  rulerLabel: string | null;
  fontSize: number;
}

/** Transient drawing feedback: rectangle in progress, open polygon, ruler. */
export function PlanPreview({ gesture, polygon, hover, ruler, rulerLabel, fontSize }: PlanPreviewProps) {
  const open = hover && polygon.length ? [...polygon, hover] : polygon;
  return (
    <g className={styles.root} aria-hidden>
      {gesture.kind === "rect" ? (
        <polygon className={styles.draft} points={toSvgPoints(rectFromCorners(gesture.a, gesture.b))} vectorEffect="non-scaling-stroke" />
      ) : null}
      {open.length > 1 ? <polyline className={styles.draft} points={toSvgPoints(open)} vectorEffect="non-scaling-stroke" /> : null}
      {polygon.map(([x, y], i) => (
        <circle key={i} className={i === 0 ? styles.first : styles.vertex} cx={x} cy={-y} r={fontSize * 0.35} />
      ))}
      {ruler.length > 0 ? (
        <polyline className={styles.ruler} points={toSvgPoints(ruler)} vectorEffect="non-scaling-stroke" />
      ) : null}
      {ruler.map(([x, y], i) => (
        <circle key={`r${i}`} className={styles.vertex} cx={x} cy={-y} r={fontSize * 0.3} />
      ))}
      {rulerLabel && ruler.length === 2 ? (
        <text
          className={styles.label}
          x={(ruler[0][0] + ruler[1][0]) / 2}
          y={-(ruler[0][1] + ruler[1][1]) / 2 - fontSize}
          fontSize={fontSize}
          textAnchor="middle"
        >
          {rulerLabel}
        </text>
      ) : null}
    </g>
  );
}
