import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { locationState } from "../../../msw/location/location.handlers";
import { renderApp, signInAs } from "../../../utils/render-app";

const P2 = "/projects/00000000-0000-4000-8000-0000000000p2/location";
const P1 = "/projects/00000000-0000-4000-8000-0000000000p1/location";

async function typeCoords(lat: string, lon: string) {
  await userEvent.type(await screen.findByLabelText("Latitud"), lat);
  await userEvent.type(screen.getByLabelText("Longitud"), lon);
  await userEvent.click(screen.getByRole("button", { name: "Fijar ubicación" }));
}

function site() {
  return within(screen.getByRole("region", { name: "Sitio" }));
}

describe("LocationStep (SCR-05)", () => {
  it("invites to choose a place and shows no site data on a new project", async () => {
    signInAs();
    renderApp(P2);
    expect(await screen.findByRole("heading", { name: "Elige dónde está tu proyecto" })).toBeInTheDocument();
    expect(screen.queryByRole("region", { name: "Sitio" })).not.toBeInTheDocument();
    expect(screen.getByText("© OpenStreetMap contributors")).toBeInTheDocument();
  });

  it("fixes the location from typed coordinates and shows elevation and density", async () => {
    signInAs();
    renderApp(P2);
    await typeCoords("4,5", "-74,25");
    expect(await screen.findByRole("region", { name: "Sitio" })).toBeInTheDocument();
    expect(site().getByText("4,50000")).toBeInTheDocument();
    expect(site().getByText("-74,25000")).toBeInTheDocument();
    expect(site().getByText(/kg\/m³/)).toBeInTheDocument();
  });

  it("explains out-of-range coordinates without calling the API", async () => {
    signInAs();
    renderApp(P2);
    await typeCoords("95", "10");
    expect(screen.getByText(/latitud va de −90 a 90/)).toBeInTheDocument();
  });

  it("fixes the location from a place search result", async () => {
    signInAs();
    renderApp(P2);
    await userEvent.type(await screen.findByLabelText("Buscar lugar"), "Puerto");
    
    await userEvent.click(await screen.findByRole("option", { name: /Puerto Ficticio/ }));
    expect(await screen.findByRole("region", { name: "Sitio" })).toBeInTheDocument();
    expect(site().getByText("-3,75000")).toBeInTheDocument();
  });

  it("asks for the altitude when the elevation service is down, then saves it", async () => {
    locationState.elevationDown = true;
    signInAs();
    renderApp(P2);
    await typeCoords("4,5", "-74,25");
    const input = await screen.findByLabelText("Altitud");
    await userEvent.type(input, "2600{Enter}");
    expect(await screen.findByText("Altitud (escrita a mano)")).toBeInTheDocument();
    expect(site().getByText("2.600 m")).toBeInTheDocument();
  });

  it("shows the saved site and the analysis height for a located project", async () => {
    signInAs();
    renderApp(P1);
    expect(await screen.findByRole("region", { name: "Sitio" })).toBeInTheDocument();
    expect(site().getByText("10,12345")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Altura de análisis" })).toHaveValue("1,5");
  });

  it("hides location controls from reviewers", async () => {
    signInAs("reviewer");
    renderApp(P1);
    await screen.findByRole("region", { name: "Sitio" });
    expect(screen.queryByLabelText("Buscar lugar")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Fijar ubicación" })).not.toBeInTheDocument();
  });
});
