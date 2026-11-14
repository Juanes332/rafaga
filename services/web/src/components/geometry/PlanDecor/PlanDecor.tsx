import { formatUnit } from "@/lib/format/format.number";
import { CompassRose } from "@/components/orientation/CompassRose/CompassRose";
import { niceScaleBar } from "@/components/geometry/PlanCanvas/PlanCanvas.utils";
import styles from "./PlanDecor.module.css";

interface PlanDecorProps {
  /** Visible span in metres and pixels per metre of the current view. */
  spanM: number;
  ppm: number;
}

/** Compass rose (plan is north-up) and metric scale bar, anchored to the canvas corner. */
export function PlanDecor({ spanM, ppm }: PlanDecorProps) {
  const metres = niceScaleBar(spanM);
  return (
    <div className={styles.root}>
      <CompassRose size={104} />
      <div className={styles.scale}>
        <div className={styles.bar} style={{ width: `${Math.round(metres * ppm)}px` }} />
        <span className="num">{formatUnit(metres, 0, "m")}</span>
      </div>
    </div>
  );
}
