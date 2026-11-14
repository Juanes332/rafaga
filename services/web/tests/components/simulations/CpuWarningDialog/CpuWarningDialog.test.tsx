import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { useSimulationFormStore } from "@/stores/simulations/simulations.store";
import { seriousViolations } from "../../../utils/axe";
import { simulationsState } from "../../../msw/simulations/simulations.handlers";
import { renderApp, signInAs } from "../../../utils/render-app";

const P1 = "/projects/00000000-0000-4000-8000-0000000000p1/simulate";

async function prepare(kind: "3D" | "Planta 2D", device: "CPU" | "GPU") {
  signInAs();
  renderApp(P1);
  await userEvent.click(await screen.findByRole("checkbox", { name: /^desde E · 90°/ }));
  await userEvent.click(screen.getByRole("radio", { name: kind }));
  await userEvent.click(screen.getByRole("radio", { name: device }));
  await screen.findByRole("region", { name: "Antes de simular" });
}

describe("CPU 3D warning (NFR-03)", () => {
  beforeEach(() => useSimulationFormStore.getState().forProject("none"));

  it("warns with the estimated time and does not launch before confirming", async () => {
    await prepare("3D", "CPU");
    const before = simulationsState.studies.length;
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));
    const dialog = await screen.findByRole("alertdialog", { name: "Esta simulación 3D será muy lenta" });
    expect(within(dialog).getByText(/no tiene tarjeta gráfica/)).toBeInTheDocument();
    expect(within(dialog).getByText(/Tiempo estimado: \d+ h/)).toBeInTheDocument();
    expect(simulationsState.studies.length).toBe(before);
  });

  it("cancel closes the dialog without launching", async () => {
    await prepare("3D", "CPU");
    const before = simulationsState.studies.length;
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));
    await userEvent.click(await screen.findByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(simulationsState.studies.length).toBe(before);
  });

  it("launches only after the explicit confirmation", async () => {
    await prepare("3D", "CPU");
    const before = simulationsState.studies.length;
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));
    await userEvent.click(await screen.findByRole("button", { name: "Lanzar en CPU" }));
    await screen.findByText("Simulación en curso").catch(() => undefined);
    expect(simulationsState.studies.length).toBe(before + 1);
  });

  it("does not interrupt a 3D run on GPU", async () => {
    await prepare("3D", "GPU");
    const before = simulationsState.studies.length;
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));
    await screen.findByText("Simulación en curso").catch(() => undefined);
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(simulationsState.studies.length).toBe(before + 1);
  });

  it("does not interrupt a 2D run on CPU", async () => {
    await prepare("Planta 2D", "CPU");
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
  });

  it("shows the node count and the NFR-03 limit", async () => {
    await prepare("3D", "CPU");
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));
    const dialog = await screen.findByRole("alertdialog");
    expect(within(dialog).getByText(/Celdas de cálculo: [\d.,\u00a0]+( M)?/)).toBeInTheDocument();
    expect(within(dialog).getByText(/Límite en CPU \(NFR-03\): 3,0 M celdas/)).toBeInTheDocument();
  });

  it("gives Cancel the initial focus", async () => {
    await prepare("3D", "CPU");
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));
    const cancel = await screen.findByRole("button", { name: "Cancelar" });
    expect(cancel).toHaveFocus();
  });

  it("closes with Escape without launching", async () => {
    await prepare("3D", "CPU");
    const before = simulationsState.studies.length;
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));
    await screen.findByRole("alertdialog");
    await userEvent.keyboard("{Escape}");
    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(simulationsState.studies.length).toBe(before);
  });

  it("disables launch with an explanation while the solver is offline", async () => {
    simulationsState.solverOffline = true;
    await prepare("3D", "CPU");
    const launch = await screen.findByRole("button", { name: "Simular" });
    expect(launch).toBeDisabled();
    const why = screen.getByText(/motor de simulación no está disponible/i, { selector: "[id='sim-offline-reason']" });
    expect(launch).toHaveAccessibleDescription(why.textContent ?? "");
  });

  it("has no serious accessibility violations in the dialog", async () => {
    await prepare("3D", "CPU");
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));
    await screen.findByRole("alertdialog");
    expect(await seriousViolations()).toEqual([]);
  });
});
