import { useTranslation } from "react-i18next";
import { degToCardinal } from "@/lib/format/format.direction";
import { cn } from "@/lib/utils";
import { useWindRose } from "./WindRose.hook";
import type { WindRoseProps } from "./WindRose.types";
import styles from "./WindRose.module.css";

const AXES = [0, 45, 90, 135, 180, 225, 270, 315];

function polar(deg: number, r: number): [number, number] {
  const a = (deg * Math.PI) / 180;
  return [Math.sin(a) * r, -Math.cos(a) * r];
}

/** 16-sector rose: petal area = frequency, colour = typical speed (cmocean speed). */
export function WindRose(props: WindRoseProps) {
  const { t } = useTranslation();
  const r = useWindRose(props);
  const size = props.size ?? 360;
  return (
    <svg
      className={styles.root}
      viewBox={`${-r.half} ${-r.half} ${size} ${size}`}
      width={size}
      height={size}
      role={r.selectable ? "group" : "img"}
      aria-label={t("wind:rose.label")}
    >
      {r.rings.map((rad) => (
        <circle key={rad} r={rad} className={styles.ring} />
      ))}
      {AXES.map((deg) => {
        const [x, y] = polar(deg, r.radius + 20);
        return (
          <text key={deg} x={x} y={y} className={cn(styles.cardinal, deg % 90 === 0 && styles.cardinalMajor)} dominantBaseline="middle" textAnchor="middle">
            <tspan x={x} dy="-0.35em">{degToCardinal(deg, 8)}</tspan>
            <tspan x={x} dy="1.25em" className={styles.degrees}>{deg}°</tspan>
          </text>
        );
      })}
      {r.petals.map((p) =>
        r.selectable ? (
          <g key={p.deg}>
            <path
              d={p.hitPath}
              role="checkbox"
              tabIndex={0}
              aria-checked={p.selected}
              aria-label={p.label}
              className={cn(styles.hit, p.selected && styles.hitSelected)}
              onClick={() => props.onToggle?.(p.deg)}
              onKeyDown={(e) => (e.key === " " || e.key === "Enter") && (e.preventDefault(), r.onKey(p.deg, e.key))}
            />
            <path d={p.path} fill={p.fill} className={styles.petal} aria-hidden />
          </g>
        ) : (
          <path key={p.deg} d={p.path} fill={p.fill} className={styles.petal}>
            <title>{p.label}</title>
          </path>
        ),
      )}
      {props.manualDeg != null ? <ManualArrow deg={props.manualDeg} radius={r.radius} /> : null}
    </svg>
  );
}

function ManualArrow({ deg, radius }: { deg: number; radius: number }) {
  const [x1, y1] = polar(deg, radius);
  const [x2, y2] = polar(deg, radius * 0.15);
  return <line x1={x1} y1={y1} x2={x2} y2={y2} className={styles.arrow} />;
}
