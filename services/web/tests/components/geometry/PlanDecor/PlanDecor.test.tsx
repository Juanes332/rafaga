import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PlanDecor } from "@/components/geometry/PlanDecor/PlanDecor";

describe("PlanDecor", () => {
  it("shows the compass rose with north up and a metric scale bar", () => {
    render(<PlanDecor spanM={200} ppm={2} />);
    expect(screen.getByRole("img", { name: /Puntos cardinales.*norte está arriba/i })).toBeInTheDocument();
    expect(screen.getByText("NO", { selector: "text" })).toBeInTheDocument();
    expect(screen.getByText(/\sm$/)).toBeInTheDocument();
  });
});
