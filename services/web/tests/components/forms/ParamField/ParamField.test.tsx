import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import { renderWithProviders } from "../../../utils/render-with-providers";

const base = { id: "h", label: "Altura", unit: "m", min: 0.5, max: 50, defaultValue: 3, value: 3 };

describe("ParamField", () => {
  it("shows default and range with units", () => {
    renderWithProviders(<ParamField {...base} onCommit={vi.fn()} />);
    expect(screen.getByText("Defecto 3,0 m. Rango 0,5–50,0 m")).toBeInTheDocument();
  });

  it("commits a comma-decimal value on Enter", async () => {
    const onCommit = vi.fn();
    renderWithProviders(<ParamField {...base} onCommit={onCommit} />);
    const input = screen.getByLabelText("Altura");
    await userEvent.clear(input);
    await userEvent.type(input, "4,5{Enter}");
    expect(onCommit).toHaveBeenCalledWith(4.5);
  });

  it("explains an out-of-range value and does not commit", async () => {
    const onCommit = vi.fn();
    renderWithProviders(<ParamField {...base} onCommit={onCommit} />);
    const input = screen.getByLabelText("Altura");
    await userEvent.clear(input);
    await userEvent.type(input, "80");
    await userEvent.tab();
    expect(screen.getByText("Escribe un valor entre 0,5 y 50,0.")).toBeInTheDocument();
    expect(onCommit).not.toHaveBeenCalled();
  });

  it("shows percent fields in 0–100 and commits a fraction", async () => {
    const onCommit = vi.fn();
    renderWithProviders(<ParamField id="p" label="Porosidad" percent min={0.05} max={0.95} value={0.4} defaultValue={0.4} onCommit={onCommit} />);
    const input = screen.getByLabelText("Porosidad");
    expect(input).toHaveValue("40");
    await userEvent.clear(input);
    await userEvent.type(input, "55{Enter}");
    expect(onCommit).toHaveBeenCalledWith(0.55);
  });

  it("announces an API adjustment", () => {
    renderWithProviders(<ParamField {...base} adjustment="Se ajustó a 12 m." onCommit={vi.fn()} />);
    expect(screen.getByRole("status")).toHaveTextContent("Se ajustó a 12 m.");
  });
});
