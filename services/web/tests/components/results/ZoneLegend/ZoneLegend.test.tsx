import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ZoneLegend } from "@/components/results/ZoneLegend/ZoneLegend";

describe("ZoneLegend", () => {
  it("lists each zone with area in m² and percent", () => {
    render(<ZoneLegend items={[{ zone: "acceleration", area_m2: 412, percent: 6.1 }, { zone: "stagnation", area_m2: 1020, percent: 13 }]} />);
    expect(screen.getByText("Aceleración")).toBeInTheDocument();
    expect(screen.getByText("1.020 m²")).toBeInTheDocument();
    expect(screen.getByText("6,1 %")).toBeInTheDocument();
  });
  it("explains when no zone passes the thresholds", () => {
    render(<ZoneLegend items={[]} />);
    expect(screen.getByText("No hay zonas con los umbrales actuales.")).toBeInTheDocument();
  });
});
