import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { LocationMap } from "@/components/location/LocationMap/LocationMap";

describe("LocationMap", () => {
  it("shows the compass rose even without WebGL, with north up", () => {
    render(<LocationMap lat={null} lon={null} onPick={vi.fn()} />);
    expect(screen.getByRole("img", { name: /Puntos cardinales.*norte está arriba/i })).toBeInTheDocument();
  });
});
