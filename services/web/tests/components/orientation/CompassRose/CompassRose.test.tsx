import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CompassRose } from "@/components/orientation/CompassRose/CompassRose";
import { compassPoints } from "@/components/orientation/CompassRose/CompassRose.utils";

describe("compassPoints", () => {
  it("places the eight Spanish points clockwise with north on top", () => {
    const pts = compassPoints(0, 10);
    expect(pts.map((p) => p.label)).toEqual(["N", "NE", "E", "SE", "S", "SO", "O", "NO"]);
    expect(pts[0].x).toBeCloseTo(0);
    expect(pts[0].y).toBeCloseTo(-10);
    expect(pts[2].x).toBeCloseTo(10);
  });
  it("turns every point with the rotation, keeping N the only major point of the cardinals", () => {
    const pts = compassPoints(90, 10);
    expect(pts[0].x).toBeCloseTo(10);
    expect(pts[0].y).toBeCloseTo(0);
    expect(pts.filter((p) => p.major).map((p) => p.label)).toEqual(["N", "E", "S", "O"]);
  });
});

describe("CompassRose", () => {
  it("is an image named with the cardinal points and says north is up", () => {
    render(<CompassRose />);
    expect(screen.getByRole("img", { name: /Puntos cardinales.*norte está arriba/i })).toBeInTheDocument();
  });

  it("shows N, NE, E, SE, S, SO, O, NO", () => {
    render(<CompassRose />);
    for (const l of ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]) {
      expect(screen.getByText(l, { selector: "text" })).toBeInTheDocument();
    }
  });

  it("emphasizes north", () => {
    render(<CompassRose />);
    expect(screen.getByText("N", { selector: "text" })).toHaveAttribute("data-north", "true");
    expect(screen.getByText("E", { selector: "text" })).not.toHaveAttribute("data-north");
  });

  it("states where north points when rotated", () => {
    render(<CompassRose rotationDeg={45} />);
    expect(screen.getByRole("img", { name: /norte.*45°/i })).toBeInTheDocument();
  });

  it("accepts an override label", () => {
    render(<CompassRose label="Orientación de la vista" />);
    expect(screen.getByRole("img", { name: "Orientación de la vista" })).toBeInTheDocument();
  });
});
