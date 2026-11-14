import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { StudySummary } from "@/types/simulations/simulation.types";
import { API } from "../../../msw/api-base";
import { reportsState } from "../../../msw/reports/reports.handlers";
import { server } from "../../../msw/server";
import { renderApp, signInAs } from "../../../utils/render-app";

const P1 = "00000000-0000-4000-8000-0000000000p1";
const P2 = "00000000-0000-4000-8000-0000000000p2";

const studies: StudySummary[] = [
  { id: "s-screen", alternative_name: "Celosía 40 %", kind: "plan2d", directions_deg: [90], status: "completed", progress: 1, device: "gpu", created_at: "2026-11-12T11:00:00Z" },
  { id: "s-base", alternative_name: "Base", kind: "plan2d", directions_deg: [90], status: "completed", progress: 1, device: "gpu", created_at: "2026-11-12T10:00:00Z" },
  { id: "s-run", alternative_name: "Aletas", kind: "plan2d", directions_deg: [90], status: "running", progress: 0.3, device: "gpu", created_at: "2026-11-12T12:00:00Z" },
];

describe("ReportsScreen (SCR-20)", () => {
  beforeEach(() => {
    server.use(http.get(`${API}/projects/:id/simulations`, ({ params }) => HttpResponse.json(params.id === P1 ? studies : [])));
  });

  it("shows the empty state with a disabled button and its reason", async () => {
    signInAs();
    renderApp(`/projects/${P2}/reports`);
    expect(await screen.findByRole("heading", { name: "Genera un informe cuando tengas resultados" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Generar informe" })[0]).toBeDisabled();
    expect(screen.getAllByText("Simula al menos una alternativa para generar un informe.").length).toBeGreaterThan(0);
  });

  it("lists versions with their status", async () => {
    signInAs();
    renderApp(`/projects/${P1}/reports`);
    const row = (await screen.findByText("v1")).closest("tr") as HTMLElement;
    expect(within(row).getByText("Informe listo")).toBeInTheDocument();
    expect(within(row).getByRole("button", { name: "Descargar PDF v1" })).toBeInTheDocument();
  });

  it("generates a report for the chosen studies against a baseline and follows it to ready", async () => {
    signInAs();
    renderApp(`/projects/${P1}/reports`);
    expect(await screen.findByRole("checkbox", { name: /Celosía 40 %/ })).toBeChecked();
    expect(screen.queryByRole("checkbox", { name: /Aletas/ })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Generar informe" }));
    await waitFor(() => expect(reportsState.requests).toHaveLength(1));
    expect(reportsState.requests[0]).toEqual({ study_ids: ["s-screen", "s-base"], baseline_study_id: "s-base", include_comfort: true });
    const row = (await screen.findByText("v2")).closest("tr") as HTMLElement;
    await waitFor(() => expect(within(row).getByText("Informe listo")).toBeInTheDocument(), { timeout: 4000 });
  });

  it("downloads a PDF through a blob", async () => {
    const createUrl = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:pdf");
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    signInAs();
    renderApp(`/projects/${P1}/reports`);
    await userEvent.click(await screen.findByRole("button", { name: "Descargar PDF v1" }));
    await waitFor(() => expect(createUrl).toHaveBeenCalled());
    expect(click).toHaveBeenCalled();
    createUrl.mockRestore();
    click.mockRestore();
  });

  it("hides generation from reviewers but keeps downloads", async () => {
    signInAs("reviewer");
    renderApp(`/projects/${P1}/reports`);
    expect(await screen.findByRole("button", { name: "Descargar PDF v1" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Generar informe" })).not.toBeInTheDocument();
    expect(screen.getByText(/puedes descargar informes, pero no generarlos/)).toBeInTheDocument();
  });
});
