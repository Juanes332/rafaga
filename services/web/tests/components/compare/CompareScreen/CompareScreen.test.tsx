import { configure, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { useCompareStore } from "@/stores/compare/compare.store";
import { P1, R1, R2, R3 } from "../../../msw/results/results.ids";
import { resultStudies, studyHandlers } from "../../../msw/results/results.studies";
import { server } from "../../../msw/server";
import { renderApp, signInAs } from "../../../utils/render-app";

// Synthetic fields are decoded in-test; under a parallel run they need more than 1 s.
configure({ asyncUtilTimeout: 5000 });

const url = (a?: string, b?: string) => `/projects/${P1}/compare${a ? `?a=${a}&b=${b}` : ""}`;

describe("CompareScreen (SCR-18)", () => {
  beforeEach(() => {
    useCompareStore.getState().reset();
    server.use(...studyHandlers());
  });

  it("picks a comparable pair by default and shows the swipe slider", async () => {
    signInAs();
    const { router } = renderApp(url());
    const slider = await screen.findByRole("slider", { name: "Posición del comparador" }, { timeout: 5000 });
    expect(slider).toHaveAttribute("aria-valuenow", "50");
    await waitFor(() => expect(router.state.location.search).toMatchObject({ a: R1, b: R2 }));
    expect(screen.getByTestId("disclaimer")).toBeInTheDocument();
  });

  it("summarises the strategy effect in plain Spanish with a verdict", async () => {
    signInAs();
    renderApp(url(R1, R2));
    const card = await screen.findByRole("region", { name: /Celosía 40 % frente a Base/ }, { timeout: 5000 });
    await waitFor(() => expect(within(card).getByText(/^Veredicto: /)).toBeInTheDocument());
    expect(within(card).getByText(/Celosía 40 % (reduce|aumenta|casi no cambia) el viento/)).toBeInTheDocument();
    expect(within(card).getByText(/Mejora|Empeora|Sin cambio relevante/)).toBeInTheDocument();
    expect(within(card).getByText("Cómo se calcula")).toBeInTheDocument();
  });

  it("moves the slider 2 % per arrow and 10 % with Shift", async () => {
    signInAs();
    renderApp(url(R1, R2));
    const slider = await screen.findByRole("slider", { name: "Posición del comparador" }, { timeout: 5000 });
    slider.focus();
    await userEvent.keyboard("{ArrowRight}");
    expect(slider).toHaveAttribute("aria-valuenow", "52");
    await userEvent.keyboard("{Shift>}{ArrowLeft}{/Shift}");
    expect(slider).toHaveAttribute("aria-valuenow", "42");
  });

  it("switches to the ΔK map with the balance legend", async () => {
    signInAs();
    renderApp(url(R1, R2));
    await screen.findByRole("slider", undefined, { timeout: 5000 });
    await userEvent.click(screen.getByRole("button", { name: "ΔK" }));
    expect(await screen.findByText("ΔK, adimensional")).toBeInTheDocument();
    expect(screen.queryByRole("slider")).not.toBeInTheDocument();
  });

  it("lists zone and Lawson areas for A and B, with the reduction for B", async () => {
    signInAs();
    renderApp(url(R1, R2));
    const table = await screen.findByRole("region", { name: "Áreas por zona y clase de confort" });
    expect(await within(table).findByText("Base, desde E · 90°")).toBeInTheDocument();
    expect(within(table).getByText("Celosía 40 %, desde E · 90°")).toBeInTheDocument();
    expect(within(table).getByRole("columnheader", { name: "Sentarse" })).toBeInTheDocument();
    await waitFor(() => expect(within(table).getAllByText(/m²/).length).toBeGreaterThan(4));
  });

  it("explains which parameters differ when results are not comparable", async () => {
    signInAs();
    renderApp(url(R1, R3));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("distinto tipo de simulación (planta 2D y 3D)");
    expect(alert).toHaveTextContent("Simula ambas alternativas con los mismos parámetros.");
  });

  it("invites to simulate when there are fewer than two results", async () => {
    server.use(...studyHandlers(resultStudies().slice(0, 1)));
    signInAs();
    renderApp(url());
    expect(await screen.findByRole("heading", { name: "Simula al menos dos alternativas en la misma dirección para compararlas" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ir a Simular" })).toBeInTheDocument();
  });

  it("swaps A and B", async () => {
    signInAs();
    const { router } = renderApp(url(R1, R2));
    await screen.findByRole("slider", undefined, { timeout: 5000 });
    await userEvent.click(screen.getByRole("button", { name: "Intercambiar A y B" }));
    await waitFor(() => expect(router.state.location.search).toMatchObject({ a: R2, b: R1 }));
  });

  it("hides export for reviewers", async () => {
    signInAs("reviewer");
    renderApp(url(R1, R2));
    await screen.findByRole("slider", undefined, { timeout: 5000 });
    expect(screen.queryByRole("button", { name: "Exportar PNG" })).not.toBeInTheDocument();
  });
});
