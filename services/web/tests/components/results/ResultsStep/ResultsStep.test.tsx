import { act, configure, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it } from "vitest";
import { useResultsStore } from "@/stores/results/results.store";
import { API } from "../../../msw/api-base";
import { P1, R1, R2, R3, R4 } from "../../../msw/results/results.ids";
import { studyHandlers } from "../../../msw/results/results.studies";
import { server } from "../../../msw/server";
import { renderApp, signInAs } from "../../../utils/render-app";

// Synthetic fields are decoded in-test; under a parallel run they need more than 1 s.
configure({ asyncUtilTimeout: 5000 });

const at = (id: string) => `/projects/${P1}/results/${id}`;

describe("ResultsStep (SCR-14)", () => {
  beforeEach(() => {
    useResultsStore.getState().reset();
    server.use(...studyHandlers());
  });

  it("shows stats, the K legend, the particle control and the disclaimer", async () => {
    signInAs();
    renderApp(at(R1));
    expect(await screen.findByText("K, adimensional")).toBeInTheDocument();
    expect(screen.getByText("0,74")).toBeInTheDocument();
    expect(screen.getByText("Base, viento desde E · 90°")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Pausar" })).toBeInTheDocument();
    expect(screen.getByTestId("disclaimer")).toBeInTheDocument();
  });

  it("explains solver warnings in plain Spanish and skips unknown codes", async () => {
    signInAs();
    renderApp(at(R2));
    const notes = await screen.findByRole("list", { name: "Avisos del cálculo" });
    expect(within(notes).getByText(/no se pueden representar en planta 2D/)).toBeInTheDocument();
    expect(within(notes).getAllByRole("listitem")).toHaveLength(1);
  });

  it("pauses with the button and with Space on the canvas", async () => {
    signInAs();
    renderApp(at(R1));
    await userEvent.click(await screen.findByRole("button", { name: "Pausar" }));
    expect(screen.getByRole("button", { name: "Reanudar" })).toBeInTheDocument();
    screen.getByRole("img", { name: "Campo de viento en planta" }).focus();
    await userEvent.keyboard(" ");
    expect(screen.getByRole("button", { name: "Pausar" })).toBeInTheDocument();
  });

  it("toggles zones and lists their areas from /zones", async () => {
    signInAs();
    renderApp(at(R1));
    await userEvent.click(await screen.findByRole("button", { name: "Zonas" }));
    const zones = await screen.findByRole("region", { name: "Zonas" });
    expect(await within(zones).findByText("Aceleración")).toBeInTheDocument();
    expect(within(zones).getAllByText(/m²/).length).toBeGreaterThan(0);
  });

  it("shows Lawson classes with coverage and a plain-language note (SCR-15)", async () => {
    signInAs();
    renderApp(at(R1));
    await userEvent.click(await screen.findByRole("radio", { name: "Lawson" }));
    expect(await screen.findByText(/Cobertura de la rosa de vientos: 97,0/)).toBeInTheDocument();
    expect(screen.queryByText("Parcial")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Sentarse/ }));
    expect(screen.getByText(/cómodo para terrazas/)).toBeInTheDocument();
  });

  it("launches a section2d study from two points and opens Simular (SCR-17)", async () => {
    let body: Record<string, unknown> | null = null;
    server.use(
      http.post(`${API}/simulations`, async ({ request }) => {
        body = (await request.json()) as Record<string, unknown>;
        return HttpResponse.json({ id: "s9", alternative_id: "a", kind: "section2d", status: "queued", progress: 0, jobs: [] }, { status: 202 });
      }),
    );
    signInAs();
    const { router } = renderApp(at(R1));
    await userEvent.click(await screen.findByRole("button", { name: /Trazar corte/ }));
    const launch = await screen.findByRole("button", { name: "Simular corte vertical" });
    expect(launch).toBeDisabled();
    act(() => {
      useResultsStore.getState().addSectionPoint([90, 10]);
      useResultsStore.getState().addSectionPoint([-20, 10]);
    });
    await userEvent.click(screen.getByRole("button", { name: "Simular corte vertical" }));
    await waitFor(() => expect(router.state.location.pathname).toMatch(/\/simulate$/));
    expect(body).toMatchObject({ kind: "section2d", section: { p0: [90, 10], p1: [-20, 10] }, dx_m: 1 });
  });

  it("warns when the section is drawn against the wind", async () => {
    signInAs();
    renderApp(at(R1));
    await userEvent.click(await screen.findByRole("button", { name: /Trazar corte/ }));
    act(() => {
      useResultsStore.getState().addSectionPoint([-20, 10]);
      useResultsStore.getState().addSectionPoint([90, 10]);
    });
    expect(await screen.findByText(/El corte va contra el viento/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Simular corte vertical" })).toBeDisabled();
  });

  it("hides export and section tools for reviewers", async () => {
    signInAs("reviewer");
    renderApp(at(R1));
    await screen.findByText("K, adimensional");
    expect(screen.queryByRole("button", { name: "Exportar PNG" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Trazar corte/ })).not.toBeInTheDocument();
  });

  it("shows a section result with height and distance axes", async () => {
    signInAs();
    renderApp(at(R4));
    expect(await screen.findByRole("img", { name: "Corte vertical de velocidad" })).toBeInTheDocument();
    expect(screen.getByText("Altura, m")).toBeInTheDocument();
    expect(screen.getByText("Velocidad, m/s")).toBeInTheDocument();
  });

  it("offers the 3D view for volume results", async () => {
    signInAs();
    renderApp(at(R3));
    expect(await screen.findByRole("button", { name: "Ver en 3D" })).toBeInTheDocument();
  });

  it("explains a missing result and links back to Simular", async () => {
    signInAs();
    renderApp(at("00000000-0000-4000-8000-00000000dead"));
    expect(await screen.findByRole("alert")).toHaveTextContent("Ese resultado ya no existe");
    expect(screen.getByRole("link", { name: "Ir a Simular" })).toBeInTheDocument();
  });
});
