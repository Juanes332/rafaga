import { useEffect, useRef, type RefObject } from "react";
import { ParticleRenderer } from "@/engines/particles/particle-gl";
import { particleCount, viewTransform } from "@/engines/particles/particles.math";
import { cssToRgba } from "@/hooks/theme/use-token-colors";
import { startLoop } from "./ParticleLayer.loop";
import type { ParticleLayerProps } from "./ParticleLayer.types";

/** Owns the GL renderer: created per field, re-viewed on pan/zoom, looped while not paused. */
export function useParticleLayer(p: ParticleLayerProps): RefObject<HTMLCanvasElement | null> {
  const ref = useRef<HTMLCanvasElement>(null);
  const renderer = useRef<ParticleRenderer | null>(null);
  const paused = useRef(p.paused);
  paused.current = p.paused;
  const { data, cols, rows, onUnavailable, width, height, view, ink } = p;
  const sized = width > 0;

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !sized) return;
    const count = particleCount({ width: window.innerWidth, dpr: window.devicePixelRatio || 1, meanFrameMs: null, area: width * height });
    const r = ParticleRenderer.create(canvas, data, cols, rows, count);
    if (!r) return onUnavailable();
    renderer.current = r;
    canvas.dataset.particles = String(r.particles); // read by scripts/measure-particle-fps.mjs
    return () => {
      r.dispose();
      renderer.current = null;
    };
    // Size changes only re-view; the particle count is fixed per field.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, cols, rows, sized, onUnavailable]);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || !renderer.current) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    renderer.current.setView({ view: viewTransform({ cols, rows, width, height, ppc: view.ppc, ox: view.ox, oy: view.oy }), ppc: view.ppc, zoom: view.zoom });
  }, [view, width, height, cols, rows, data]);

  useEffect(() => {
    const r = renderer.current;
    if (!r) return;
    const canvas = ref.current;
    return startLoop(r, cssToRgba(ink, 0.7), () => paused.current, (n) => {
      if (canvas) canvas.dataset.particles = String(n);
    });
  }, [ink, data, sized]);
  return ref;
}
