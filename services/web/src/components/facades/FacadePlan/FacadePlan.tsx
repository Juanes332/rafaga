import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";
import { useFacadePlan } from "./FacadePlan.hook";
import type { FacadePlanProps } from "./FacadePlan.types";
import styles from "./FacadePlan.module.css";

/** Read-only plan; each façade edge is a button when strategies can be added. */
export function FacadePlan(props: FacadePlanProps) {
  const { t } = useTranslation();
  const { viewBox, buildings } = useFacadePlan(props);
  const vb = `${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`;
  return (
    <svg className={styles.root} viewBox={vb} preserveAspectRatio="xMidYMid meet" role="group" aria-label={t("alternatives:plan.label")}>
      {buildings.map((b) => (
        <g key={b.id}>
          <polygon points={b.points} className={styles.building} />
          <text x={b.centre[0]} y={b.centre[1]} className={styles.name} style={{ fontSize: viewBox.width / 55 }} textAnchor="middle" dominantBaseline="middle" aria-hidden>
            {b.name}
          </text>
          {b.edges.map((e) =>
            e.strategySegment ? (
              <line
                key={`${e.key}-s`}
                x1={e.strategySegment[0]}
                y1={e.strategySegment[1]}
                x2={e.strategySegment[2]}
                y2={e.strategySegment[3]}
                className={cn(styles.strategy, styles[e.strategy ?? "screen"])}
                aria-hidden
              />
            ) : null,
          )}
          {b.edges.map((e) => (
            <line
              key={e.key}
              x1={e.a[0]}
              y1={-e.a[1]}
              x2={e.b[0]}
              y2={-e.b[1]}
              className={cn(styles.edge, e.selected && styles.selected, props.interactive && styles.pickable)}
              role={props.interactive ? "button" : undefined}
              tabIndex={props.interactive ? 0 : undefined}
              aria-pressed={props.interactive ? e.selected : undefined}
              aria-label={props.interactive ? e.label : undefined}
              onClick={props.interactive ? () => props.onSelect({ buildingId: e.buildingId, edgeIndex: e.index }) : undefined}
              onKeyDown={
                props.interactive
                  ? (ev) => (ev.key === "Enter" || ev.key === " ") && (ev.preventDefault(), props.onSelect({ buildingId: e.buildingId, edgeIndex: e.index }))
                  : undefined
              }
            />
          ))}
        </g>
      ))}
      <NorthArrow x={viewBox.x + viewBox.width - viewBox.width / 30} y={viewBox.y + viewBox.width / 30} size={viewBox.width / 40} />
    </svg>
  );
}

function NorthArrow({ x, y, size }: { x: number; y: number; size: number }) {
  return (
    <g className={styles.north} aria-hidden>
      <path d={`M${x},${y - size} L${x + size * 0.45},${y + size * 0.6} L${x},${y + size * 0.25} L${x - size * 0.45},${y + size * 0.6} Z`} />
      <text x={x} y={y + size * 1.6} textAnchor="middle" style={{ fontSize: size * 0.9 }}>
        N
      </text>
    </g>
  );
}
