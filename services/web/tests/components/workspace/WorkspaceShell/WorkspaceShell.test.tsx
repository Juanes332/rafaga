import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { systemState } from "../../../msw/system/system.handlers";
import { renderApp, signInAs } from "../../../utils/render-app";

const P2 = "/projects/00000000-0000-4000-8000-0000000000p2/location";

describe("WorkspaceShell (SCR-04)", () => {
  it("shows the project in the breadcrumb and the compute badge", async () => {
    signInAs();
    renderApp(P2);
    const crumbs = await screen.findByRole("navigation", { name: "Ruta" });
    expect(await within(crumbs).findByText("Conjunto norte")).toBeInTheDocument();
    expect(await screen.findByText("GPU: NVIDIA RTX 4060")).toBeInTheDocument();
  });

  it("locks Viento with the reason while the project has no location", async () => {
    signInAs();
    renderApp(P2);
    const rail = await screen.findByRole("navigation", { name: "Pasos del proyecto" });
    const wind = await within(rail).findByRole("button", { name: /Viento/ });
    expect(wind).toHaveAttribute("aria-disabled", "true");
    expect(wind).toHaveTextContent("Fija la ubicación");
  });

  it("reports CPU cores when no GPU is present", async () => {
    systemState.status = { ...systemState.status, solver: { ...systemState.status.solver, device: "cpu", gpu_name: null } };
    signInAs();
    renderApp(P2);
    expect(await screen.findByText("CPU: 16 núcleos")).toBeInTheDocument();
  });

  it("cycles the theme from the top bar", async () => {
    signInAs();
    renderApp(P2);
    await userEvent.click(await screen.findByRole("button", { name: /Cambiar tema/ }));
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });
});
