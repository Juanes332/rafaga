import { useParticleLayer } from "./ParticleLayer.hook";
import type { ParticleLayerProps } from "./ParticleLayer.types";

/** The memorable element: wind made visible as drifting ink over the K field. */
export function ParticleLayer(props: ParticleLayerProps) {
  const ref = useParticleLayer(props);
  return <canvas ref={ref} className={props.className} style={{ width: props.width, height: props.height }} aria-hidden />;
}
