import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";
import { compassPoints } from "./CompassRose.utils";
import type { CompassRoseProps } from "./CompassRose.types";
import styles from "./CompassRose.module.css";

const HALF = 60;
const LABEL_RADIUS = 46;

function useCompassLabel(rotationDeg: number, label?: string): string {
  const { t } = useTranslation();
  if (label) return label;
  const deg = Math.round(((rotationDeg % 360) + 360) % 360);
  const where = deg === 0 ? t("orientation:compass.northUp") : t("orientation:compass.northRotated", { deg });
  return `${t("orientation:compass.label")} ${where}`;
}

/** Eight-point Spanish compass rose; N is emphasized and the needle follows `rotationDeg`. */
export function CompassRose({ size = 104, rotationDeg = 0, label, className }: CompassRoseProps) {
  const name = useCompassLabel(rotationDeg, label);
  const points = compassPoints(rotationDeg, LABEL_RADIUS);
  return (
    <svg
      className={cn(styles.root, className)}
      viewBox={`${-HALF} ${-HALF} ${HALF * 2} ${HALF * 2}`}
      width={size}
      height={size}
      role="img"
      aria-label={name}
    >
      <circle r={30} className={styles.ring} />
      <g transform={`rotate(${rotationDeg})`} aria-hidden>
        <path d="M0 -32 L7 0 L0 -5 L-7 0 Z" className={styles.needleNorth} />
        <path d="M0 32 L7 0 L0 5 L-7 0 Z" className={styles.needleSouth} />
      </g>
      {points.map((p) => (
        <text
          key={p.label}
          x={p.x}
          y={p.y}
          textAnchor="middle"
          dominantBaseline="central"
          className={cn(styles.label, p.major && styles.major, p.north && styles.north)}
          data-north={p.north || undefined}
          aria-hidden
        >
          {p.label}
        </text>
      ))}
    </svg>
  );
}
