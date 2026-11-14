import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { startLoop } from "@/components/results/ParticleLayer/ParticleLayer.loop";
import type { ParticleRenderer } from "@/engines/particles/particle-gl";

type Cb = (t: number) => void;

function fakeRenderer(particles: number) {
  const r = { particles, frame: vi.fn(), setCount: vi.fn((n: number) => (r.particles = n)) };
  return r;
}

describe("startLoop", () => {
  let queue: Cb[] = [];
  beforeEach(() => {
    queue = [];
    vi.stubGlobal("requestAnimationFrame", (cb: Cb) => queue.push(cb));
    vi.stubGlobal("cancelAnimationFrame", vi.fn());
  });
  afterEach(() => vi.unstubAllGlobals());

  const run = (frames: number, stepMs: number) => {
    let t = 1000;
    for (let i = 0; i < frames; i += 1) {
      t += stepMs;
      queue.shift()?.(t);
    }
  };

  it("halves particles when frames arrive slowly even though submission is cheap", () => {
    const r = fakeRenderer(16384);
    startLoop(r as unknown as ParticleRenderer, [0, 0, 0, 1], () => false);
    run(40, 40); // 25 fps: a GPU-bound frame costs nothing on the CPU side
    expect(r.setCount).toHaveBeenCalledWith(8192);
  });

  it("reports the new count when it degrades", () => {
    const r = fakeRenderer(16384);
    const onCount = vi.fn();
    startLoop(r as unknown as ParticleRenderer, [0, 0, 0, 1], () => false, onCount);
    run(40, 40);
    expect(onCount).toHaveBeenCalledWith(8192);
  });

  it("keeps particles at a steady 60 fps", () => {
    const r = fakeRenderer(16384);
    startLoop(r as unknown as ParticleRenderer, [0, 0, 0, 1], () => false);
    run(120, 16.7);
    expect(r.setCount).not.toHaveBeenCalled();
  });

  it("ignores long gaps such as a backgrounded tab", () => {
    const r = fakeRenderer(16384);
    startLoop(r as unknown as ParticleRenderer, [0, 0, 0, 1], () => false);
    run(60, 16.7);
    run(1, 5000);
    run(20, 16.7);
    expect(r.setCount).not.toHaveBeenCalled();
  });

  it("never drops below the floor", () => {
    const r = fakeRenderer(2048);
    startLoop(r as unknown as ParticleRenderer, [0, 0, 0, 1], () => false);
    run(100, 50);
    expect(r.setCount).not.toHaveBeenCalled();
  });
});
