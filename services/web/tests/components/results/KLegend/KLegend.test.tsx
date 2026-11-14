import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { KLegend } from "@/components/results/KLegend/KLegend";

describe("KLegend", () => {
  it("labels the unit and shows the fixed 0–2 ticks in es-CO", () => {
    render(<KLegend kind="k" marks={[0.3, 1.2]} />);
    expect(screen.getByText("K, adimensional")).toBeInTheDocument();
    for (const tick of ["0,0", "0,3", "0,6", "1,0", "1,2", "1,6", "2,0"]) expect(screen.getByText(tick)).toBeInTheDocument();
  });
  it("announces saturation above the domain", () => {
    render(<KLegend kind="k" />);
    expect(screen.getByRole("img", { name: "Valores mayores que 2,0 se muestran con el color del extremo" })).toBeInTheDocument();
  });
  it("uses a symmetric signed scale for ΔK", () => {
    render(<KLegend kind="dk" marks={[-0.1]} />);
    expect(screen.getByText("ΔK, adimensional")).toBeInTheDocument();
    expect(screen.getByText("-0,6")).toBeInTheDocument();
    expect(screen.getByText("+0,6")).toBeInTheDocument();
  });
  it("scales the speed legend to the field maximum in m/s", () => {
    render(<KLegend kind="speed" max={7.3} />);
    expect(screen.getByText("Velocidad, m/s")).toBeInTheDocument();
    expect(screen.getByText("8")).toBeInTheDocument();
  });
});
