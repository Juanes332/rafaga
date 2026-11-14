import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { useSimulationFormStore } from "@/stores/simulations/simulations.store";
import { simulationsState } from "../../../msw/simulations/simulations.handlers";
import { renderApp, signInAs } from "../../../utils/render-app";

const P1 = "/projects/00000000-0000-4000-8000-0000000000p1/simulate";
const P2 = "/projects/00000000-0000-4000-8000-0000000000p2/simulate";

async function pickEast() {
  await userEvent.click(await screen.findByRole("checkbox", { name: /^desde E · 90°/ }));
}

describe("SimulateStep (SCR-12)", () => {
  beforeEach(() => useSimulationFormStore.getState().forProject("none"));

  it("shows the coverage of the chosen directions", async () => {
    signInAs();
    renderApp(P1);
    await pickEast();
    expect(screen.getByText("1 dirección elegida")).toBeInTheDocument();
    expect(screen.getByText("Cubren el 20,0 % del tiempo")).toBeInTheDocument();
  });

  it("estimates before launching and launches a study", async () => {
    signInAs();
    renderApp(P1);
    await pickEast();
    const estimate = await screen.findByRole("region", { name: "Antes de simular" });
    expect(await within(estimate).findByText("Cabe en la memoria disponible.")).toBeInTheDocument();
    const before = simulationsState.studies.length;
    await userEvent.click(screen.getByRole("button", { name: "Simular" }));
    await screen.findByText("Simulación en curso").catch(() => undefined);
    expect(simulationsState.studies.length).toBe(before + 1);
  });

  it("offers the proposed cell size when the mesh does not fit", async () => {
    signInAs();
    renderApp(P1);
    await pickEast();
    await userEvent.click(screen.getByRole("radio", { name: "3D" }));
    const dx = screen.getByRole("textbox", { name: "Tamaño de celda" });
    await userEvent.clear(dx);
    await userEvent.type(dx, "0,25{Enter}");
    const offer = await screen.findByRole("button", { name: /^Usar celda de/ });
    await userEvent.click(offer);
    expect(dx).not.toHaveValue("0,25");
  });

  it("asks for a direction before launching", async () => {
    signInAs();
    renderApp(P1);
    await userEvent.click(await screen.findByRole("button", { name: "Simular" }));
    expect(await screen.findByText("Elige al menos una dirección del viento.")).toBeInTheDocument();
  });

  it("explains that sections are drawn on the results plan", async () => {
    signInAs();
    renderApp(P1);
    await userEvent.click(await screen.findByRole("radio", { name: "Corte vertical" }));
    expect(screen.getByText(/El corte se traza sobre la planta/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Simular" })).toBeDisabled();
  });

  it("stays locked until the project has a location", async () => {
    signInAs();
    renderApp(P2);
    expect(await screen.findByRole("alert")).toHaveTextContent(/^Fija la ubicación del proyecto/);
  });
});

describe("jobs and progress (SCR-13)", () => {
  it("shows per-direction progress with phase, ETA and device", async () => {
    signInAs();
    renderApp(P1);
    expect(await screen.findByRole("progressbar", { name: "Progreso de la simulación desde E · 90°" })).toBeInTheDocument();
    expect(await screen.findByText(/Promediando el viento\. Quedan .*\. En GPU/)).toBeInTheDocument();
  });

  it("explains a failed job and resumes it", async () => {
    signInAs();
    renderApp(P1);
    expect(await screen.findByText(/El motor se reinició mientras simulaba/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Reanudar simulación desde ESE · 112,5°" }));
    expect(await screen.findByRole("progressbar", { name: "Progreso de la simulación desde ESE · 112,5°" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reanudar simulación desde ESE · 112,5°" })).not.toBeInTheDocument();
  });

  it("links completed jobs to their result and offers comparison", async () => {
    signInAs();
    renderApp(P1);
    const links = await screen.findAllByRole("link", { name: "Ver resultado desde E · 90°" });
    expect(links[0]).toHaveAttribute("href", expect.stringMatching(/\/results\/00000000-0000-4000-8000-0000000000r2$/));
    expect(screen.getByRole("link", { name: "Comparar resultados" })).toBeInTheDocument();
  });

  it("cancels a running study", async () => {
    signInAs();
    renderApp(P1);
    await userEvent.click(await screen.findByRole("button", { name: "Cancelar simulación" }));
    expect((await screen.findAllByText("Cancelada")).length).toBeGreaterThan(0);
  });

  it("hides launch and cancel controls from reviewers", async () => {
    signInAs("reviewer");
    renderApp(P1);
    await screen.findByRole("progressbar", { name: "Progreso de la simulación desde E · 90°" });
    expect(screen.queryByRole("button", { name: "Simular" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Cancelar simulación" })).not.toBeInTheDocument();
  });
});
