import { useTranslation } from "react-i18next";
import { BuildingShape } from "@/components/geometry/BuildingShape/BuildingShape";
import { PlanBackground } from "@/components/geometry/PlanBackground/PlanBackground";
import { PlanDecor } from "@/components/geometry/PlanDecor/PlanDecor";
import { PlanPreview } from "@/components/geometry/PlanPreview/PlanPreview";
import { formatUnit } from "@/lib/format/format.number";
import { cn } from "@/lib/utils";
import { usePlanCanvas } from "./PlanCanvas.hook";
import type { PlanCanvasProps } from "./PlanCanvas.types";
import { gridPath } from "./PlanCanvas.utils";
import styles from "./PlanCanvas.module.css";

/** SVG plan in metres, north up, 1 m / 10 m grid. */
export function PlanCanvas(props: PlanCanvasProps) {
  const { t } = useTranslation();
  const c = usePlanCanvas(props);
  const { vb } = c;
  const font = 13 / c.ppm;
  const unnamed = t("geometry:canvas.unnamed");
  return (
    <div className={styles.root}>
      <svg
        ref={c.svgRef}
        className={cn(styles.svg, styles[c.tool])}
        viewBox={`${vb.x} ${vb.y} ${vb.w} ${vb.h}`}
        preserveAspectRatio="xMidYMid meet"
        role="application"
        aria-label={t("geometry:canvas.label")}
        tabIndex={0}
        onPointerDown={c.onPointerDown}
        onPointerMove={c.onPointerMove}
        onPointerUp={c.onPointerUp}
        onDoubleClick={c.onDoubleClick}
        onKeyDown={c.onKeyDown}
      >
        {c.ppm >= 4 ? <path className={styles.minor} d={gridPath(vb, 1)} vectorEffect="non-scaling-stroke" /> : null}
        <path className={styles.major} d={gridPath(vb, 10)} vectorEffect="non-scaling-stroke" />
        <PlanBackground projectId={props.projectId} />
        {c.buildings.map((b) => (
          <BuildingShape
            key={b.id}
            building={b}
            selected={b.id === c.selectedId}
            offset={c.gesture.kind === "move" && c.gesture.id === b.id ? c.gesture.delta : null}
            interactive={!props.readOnly}
            label={t("geometry:canvas.building", { name: b.name ?? unnamed, height: formatUnit(b.height_m, 1, "m") })}
            heightText={formatUnit(b.height_m, 1, "m")}
            fontSize={font}
            onPointerDown={c.onShapePointerDown}
            onKeyDown={c.onShapeKey}
          />
        ))}
        <PlanPreview
          gesture={c.gesture}
          polygon={c.polygon.points}
          hover={c.polygon.hover}
          ruler={c.ruler.points}
          rulerLabel={c.rulerLabel}
          fontSize={font}
        />
      </svg>
      <PlanDecor spanM={vb.w} ppm={c.ppm} />
      {c.polygon.points.length > 0 ? (
        <p className={styles.status} role="status">
          {t("geometry:canvas.drawing", { count: c.polygon.points.length })}
        </p>
      ) : null}
    </div>
  );
}
