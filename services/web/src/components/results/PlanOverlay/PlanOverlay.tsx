import { useTranslation } from "react-i18next";
import { cellToScreen, enuToCell } from "@/engines/fields/grid-view";
import type { PlanOverlayProps } from "./PlanOverlay.types";
import styles from "./PlanOverlay.module.css";

/** Buildings, zone labels and the section line, drawn in screen pixels over the field. */
export function PlanOverlay({ view, grid, buildings, labels, section }: PlanOverlayProps) {
  const { t } = useTranslation();
  const toScreen = (x: number, y: number) => {
    const [cx, cy] = enuToCell(grid, x, y);
    return cellToScreen(view, grid.ny, cx, cy);
  };
  const pts = section.map(([x, y]) => toScreen(x, y));
  return (
    <g>
      <defs>
        <marker id="section-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="var(--color-accent)" />
        </marker>
      </defs>
      {buildings.map((b) => (
        <polygon key={b.id} className={styles.building} points={b.footprint.map(([x, y]) => toScreen(x, y).join(",")).join(" ")} />
      ))}
      {labels
        .filter((l) => l.blob.cells * view.ppc * view.ppc > 400)
        .map((l) => {
          const [x, y] = cellToScreen(view, grid.ny, l.blob.col, l.blob.row);
          return (
            <text key={l.zone} x={x} y={y} className={styles[l.zone]} textAnchor="middle">
              {t(`results:zone.${l.zone}`)}
            </text>
          );
        })}
      {pts.length === 2 ? (
        <line x1={pts[0][0]} y1={pts[0][1]} x2={pts[1][0]} y2={pts[1][1]} className={styles.section} markerEnd="url(#section-arrow)" />
      ) : null}
      {pts.map(([x, y], i) => (
        <g key={i}>
          <circle cx={x} cy={y} r={5} className={styles.point} />
          <text x={x + 8} y={y - 8} className={styles.pointLabel}>
            {i === 0 ? t("results:section.upwind") : t("results:section.downwind")}
          </text>
        </g>
      ))}
    </g>
  );
}
