import type { ReactNode } from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// No WebGL in jsdom: the canvas becomes a plain div that forwards its DOM props.
vi.mock("@react-three/fiber", () => ({
  Canvas: ({ children: _c, camera: _cam, ...rest }: { children: ReactNode; camera: unknown }) => <div {...rest} />,
  useFrame: vi.fn(),
  useThree: vi.fn(),
}));
vi.mock("@react-three/drei", () => ({ Edges: () => null, OrbitControls: () => null }));
vi.mock("@/components/geometry/Geometry3D/Geometry3D.data", () => ({ useGeometry3DData: () => [] }));

import { Geometry3DView } from "@/components/geometry/Geometry3DView/Geometry3DView";

describe("Geometry3DView accessibility", () => {
  it("keeps the compass outside the scene image so its name is not presentational", () => {
    render(<Geometry3DView alternativeId={null} label="Vista 3D" />);
    const scene = screen.getByRole("img", { name: "Vista 3D" });
    const compass = screen.getByRole("img", { name: /Puntos cardinales/ });
    expect(scene.contains(compass)).toBe(false);
  });
});
