import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { WindRose } from "@/components/wind/WindRose/WindRose";
import { eraSectors } from "../../../msw/wind/wind.fixtures";

describe("WindRose", () => {
  it("labels each sector with direction, frequency and typical speed", () => {
    render(<WindRose sectors={eraSectors()} />);
    expect(screen.getByRole("img", { name: /Rosa de vientos/ })).toBeInTheDocument();
    expect(screen.getByText(/^desde E · 90°: 20,0/)).toBeInTheDocument();
  });

  it("labels the axes with cardinal name and degrees, all eight points", () => {
    render(<WindRose sectors={eraSectors()} />);
    for (const l of ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]) {
      expect(screen.getByText(l, { selector: "text > tspan:first-child" })).toBeInTheDocument();
    }
    expect(screen.getByText("0°", { selector: "tspan" })).toBeInTheDocument();
    expect(screen.getByText("270°", { selector: "tspan" })).toBeInTheDocument();
    expect(screen.getByText("45°", { selector: "tspan" })).toBeInTheDocument();
  });

  it("toggles directions by click and keyboard in selection mode", async () => {
    const onToggle = vi.fn();
    render(<WindRose sectors={eraSectors()} selected={[90]} onToggle={onToggle} />);
    const east = screen.getByRole("checkbox", { name: /^desde E · 90°/ });
    expect(east).toHaveAttribute("aria-checked", "true");
    await userEvent.click(screen.getByRole("checkbox", { name: /^desde ENE/ }));
    expect(onToggle).toHaveBeenCalledWith(67.5);
    east.focus();
    await userEvent.keyboard(" ");
    expect(onToggle).toHaveBeenCalledWith(90);
  });
});
