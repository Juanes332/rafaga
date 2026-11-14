import { useTraceImage } from "./TraceImage.hook";
import type { TraceImageProps } from "./TraceImage.types";
import styles from "./TraceImage.module.css";

/** Plan page with picked points drawn on top. */
export function TraceImage(props: TraceImageProps) {
  const v = useTraceImage(props);
  const r = Math.max(v.natural[0], v.natural[1]) / 150;
  return (
    <div className={styles.root} onClick={v.onClick}>
      <img src={props.url} alt={props.alt} className={styles.img} onLoad={v.onLoad} draggable={false} />
      <svg className={styles.overlay} viewBox={`0 0 ${v.natural[0]} ${v.natural[1]}`} preserveAspectRatio="none" aria-hidden>
        {props.points.length === 2 ? (
          <line x1={props.points[0][0]} y1={props.points[0][1]} x2={props.points[1][0]} y2={props.points[1][1]} vectorEffect="non-scaling-stroke" />
        ) : null}
        {props.points.map(([x, y], i) => (
          <circle key={i} cx={x} cy={y} r={r} />
        ))}
      </svg>
    </div>
  );
}
