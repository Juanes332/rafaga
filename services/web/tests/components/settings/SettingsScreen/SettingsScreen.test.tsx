import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { settingsState } from "../../../msw/settings/settings.handlers";
import { renderApp, signInAs } from "../../../utils/render-app";

async function setField(label: string, value: string) {
  const input = await screen.findByLabelText(label);
  await userEvent.clear(input);
  await userEvent.type(input, `${value}{Enter}`);
}

describe("SettingsScreen (SCR-21)", () => {
  it("loads current thresholds with a plain-language note", async () => {
    signInAs();
    renderApp("/settings");
    expect(await screen.findByLabelText("Aceleración: K mayor que")).toHaveValue("1,20");
    expect(screen.getByText(/Zonas donde K supera 1,20/)).toBeInTheDocument();
  });

  it("saves edited values with PATCH /settings", async () => {
    signInAs();
    renderApp("/settings");
    await setField("Aceleración: K mayor que", "1,4");
    await setField("Coeficiente de arrastre de vegetación", "0,3");
    await userEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    await waitFor(() => expect(settingsState.patches).toHaveLength(1));
    expect(settingsState.patches[0]).toMatchObject({ thresholds: { k_accel: 1.4 }, vegetation_cd: 0.3 });
    expect(settingsState.settings.thresholds.k_accel).toBe(1.4);
  });

  it("blocks saving when Lawson thresholds do not increase", async () => {
    signInAs();
    renderApp("/settings");
    await setField("Estar de pie", "3");
    expect(screen.getByText("Los umbrales deben crecer de una actividad a la siguiente.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guardar cambios" })).toBeDisabled();
  });

  it("shows an inline range error from a 422 next to the field", async () => {
    signInAs();
    renderApp("/settings");
    await setField("Máximo de alternativas por proyecto", "21");
    // ParamField rejects 21 locally (range 1–20), so nothing is sent.
    expect(screen.getByText("Escribe un valor entre 1 y 20.")).toBeInTheDocument();
    expect(settingsState.patches).toHaveLength(0);
  });
});
