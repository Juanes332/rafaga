import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { windState } from "../../../msw/wind/wind.handlers";
import { renderApp, signInAs } from "../../../utils/render-app";

const P1 = "/projects/00000000-0000-4000-8000-0000000000p1/wind";
const P2 = "/projects/00000000-0000-4000-8000-0000000000p2/wind";

describe("WindStep (SCR-10)", () => {
  it("shows the 16-sector rose and the per-sector table", async () => {
    signInAs();
    renderApp(P1);
    expect(await screen.findByRole("img", { name: /Rosa de vientos/ })).toBeInTheDocument();
    const table = screen.getByRole("table");
    expect(within(table).getAllByRole("row")).toHaveLength(17);
    expect(within(table).getByText("desde E · 90°")).toBeInTheDocument();
  });

  it("shows the air density with its formula", async () => {
    signInAs();
    renderApp(P1);
    expect(await screen.findByText(/ρ = 1,225/)).toBeInTheDocument();
    expect(screen.getByText("1,129 kg/m³")).toBeInTheDocument();
  });

  it("asks for the location first when the project has none", async () => {
    signInAs();
    renderApp(P2);
    expect(await screen.findByRole("alert")).toHaveTextContent(/^Fija la ubicación del proyecto/);
  });

  it("fetches ERA5 for a located project without a rose", async () => {
    windState.byProject = {};
    signInAs();
    renderApp(P1);
    await userEvent.click(await screen.findByRole("button", { name: "Descargar viento histórico" }));
    expect(await screen.findByRole("img", { name: /Rosa de vientos/ })).toBeInTheDocument();
  });

  it("explains offline ERA5 and offers manual entry", async () => {
    windState.byProject = {};
    windState.era5Offline = true;
    signInAs();
    renderApp(P1);
    await userEvent.click(await screen.findByRole("button", { name: "Descargar viento histórico" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/no hay conexión y este sitio no está en caché/);
    await userEvent.click(within(alert).getByRole("button", { name: "Escribir viento a mano" }));
    expect(await screen.findByLabelText("Velocidad de referencia a 10 m")).toBeInTheDocument();
    expect(screen.getByText(/Sopla desde E · 90°/)).toBeInTheDocument();
  });

  it("fills z0 from the terrain category", async () => {
    signInAs();
    renderApp(P1);
    const z0 = await screen.findByLabelText("Rugosidad (z0)");
    expect(z0).toHaveValue("1,0000");
    await userEvent.click(screen.getByRole("combobox", { name: "Tipo de terreno alrededor" }));
    await userEvent.click(await screen.findByRole("option", { name: "Suburbano" }));
    expect(await screen.findByDisplayValue("0,3000")).toBeInTheDocument();
  });
});
