import { FrameBudget } from "@/engines/particles/particles.math";
import type { ParticleRenderer } from "@/engines/particles/particle-gl";

const MIN_PARTICLES = 2048;
// A longer gap is a stalled tab or a pause, not rendering cost
const MAX_SAMPLE_MS = 250;

/** rAF loop: skips while hidden or paused, halves particles if 30 frame intervals average > 20 ms. */
export function startLoop(r: ParticleRenderer, color: [number, number, number, number], isPaused: () => boolean, onCount?: (particles: number) => void): () => void {
  const budget = new FrameBudget();
  let raf = 0;
  let last: number | null = null;
  const tick = (now: number) => {
    raf = requestAnimationFrame(tick);
    if (isPaused() || document.hidden) {
      last = null;
      return;
    }
    r.frame(color);
    // Frame interval, not submission time: a GPU-bound frame costs the CPU almost nothing.
    if (last !== null && now - last < MAX_SAMPLE_MS) budget.push(now - last);
    last = now;
    if (budget.shouldDegrade() && r.particles > MIN_PARTICLES) {
      r.setCount(Math.max(MIN_PARTICLES, r.particles / 2));
      onCount?.(r.particles);
    }
  };
  raf = requestAnimationFrame(tick);
  return () => cancelAnimationFrame(raf);
}
