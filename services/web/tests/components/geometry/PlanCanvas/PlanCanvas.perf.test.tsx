import { act, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PlanCanvas } from "@/components/geometry/PlanCanvas/PlanCanvas";
import { updateBuilding } from "@/engines/geometry/buildings";
import { useGeometryStore } from "@/stores/geometry/geometry.store";
import type { Building } from "@/types/geometry/geometry.types";
import { renderWithProviders } from "../../../utils/render-with-providers";

function blocks(n: number): Building[] {
  return Array.from({ length: n }, (_, i) => {
    const x = (i % 20) * 15;
    const y = Math.floor(i / 20) * 15;
    return { id: `b${i}`, name: `B${i}`, footprint: [[x, y], [x + 10, y], [x + 10, y + 10], [x, y + 10]], holes: [], height_m: 12, source: "draw", missing_height: false };
  });
}

describe("PlanCanvas performance (NFR-04)", () => {
  it("keeps p95 edit latency under 100 ms with 200 blocks", async () => {
    useGeometryStore.getState().load("perf", { version: 1, buildings: blocks(200), issues: [] });
    renderWithProviders(<PlanCanvas projectId="perf" readOnly={false} />);
    expect(await screen.findAllByRole("button")).toHaveLength(200);
    const times: number[] = [];
    for (let i = 0; i < 40; i += 1) {
      const t0 = performance.now();
      act(() => {
        const s = useGeometryStore.getState();
        s.apply(updateBuilding(s.buildings, `b${i}`, { height_m: 20 + i }));
        s.select(`b${i}`);
      });
      times.push(performance.now() - t0);
    }
    times.sort((a, b) => a - b);
    expect(times[Math.floor(times.length * 0.95)]).toBeLessThan(100);
  });
});
