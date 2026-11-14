import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { CoordinateForm } from "@/components/location/CoordinateForm/CoordinateForm";

function setup() {
  const onSubmit = vi.fn();
  render(<CoordinateForm lat={null} lon={null} pending={false} onSubmit={onSubmit} />);
  return onSubmit;
}

describe("CoordinateForm notations", () => {
  it("submits degrees, minutes and seconds with hemisphere letters", async () => {
    const onSubmit = setup();
    await userEvent.type(screen.getByLabelText("Latitud"), `5°32'13"N`);
    await userEvent.type(screen.getByLabelText("Longitud"), `73°21'38"O`);
    await userEvent.click(screen.getByRole("button", { name: "Fijar ubicación" }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit.mock.calls[0][0]).toBeCloseTo(5.536944, 5);
    expect(onSubmit.mock.calls[0][1]).toBeCloseTo(-73.360556, 5);
  });

  it("splits a whole position pasted in the latitude field", async () => {
    const onSubmit = setup();
    await userEvent.click(screen.getByLabelText("Latitud"));
    await userEvent.paste(`5 32.2 N, 73 21.6 W`);
    await userEvent.click(screen.getByRole("button", { name: "Fijar ubicación" }));
    expect(onSubmit.mock.calls[0][0]).toBeCloseTo(5 + 32.2 / 60, 6);
    expect(onSubmit.mock.calls[0][1]).toBeCloseTo(-(73 + 21.6 / 60), 6);
  });

  it("explains the accepted formats when the text cannot be read", async () => {
    const onSubmit = setup();
    await userEvent.type(screen.getByLabelText("Latitud"), "aquí");
    await userEvent.type(screen.getByLabelText("Longitud"), "allá");
    await userEvent.click(screen.getByRole("button", { name: "Fijar ubicación" }));
    expect(screen.getByRole("alert")).toHaveTextContent(/grados, minutos y segundos/);
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
