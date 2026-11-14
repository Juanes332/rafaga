import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { projectsState } from "../../../msw/projects/projects.handlers";
import { renderApp, signInAs } from "../../../utils/render-app";

describe("ProjectsScreen (SCR-03)", () => {
  it("lists projects with location state and last update", async () => {
    signInAs();
    renderApp("/projects");
    const row = (await screen.findByRole("link", { name: "Conjunto norte" })).closest("tr") as HTMLElement;
    expect(within(row).getByText("Sin ubicación")).toBeInTheDocument();
    expect(screen.getByText("Ubicación fijada")).toBeInTheDocument();
  });

  it("invites to create the first project when the list is empty", async () => {
    projectsState.projects = [];
    signInAs();
    renderApp("/projects");
    expect(await screen.findByRole("heading", { name: "Crea tu primer proyecto" })).toBeInTheDocument();
  });

  it("creates a project and opens its location step", async () => {
    signInAs();
    const { router } = renderApp("/projects");
    await userEvent.click(await screen.findByRole("button", { name: "Nuevo proyecto" }));
    await userEvent.type(screen.getByLabelText("Nombre del proyecto"), "Torre sur");
    await userEvent.click(screen.getByRole("button", { name: "Crear proyecto" }));
    await screen.findByRole("navigation", { name: "Pasos del proyecto" });
    expect(router.state.location.pathname).toMatch(/\/location$/);
  });

  it("asks for confirmation naming the project before deleting", async () => {
    signInAs();
    renderApp("/projects");
    await userEvent.click(await screen.findByRole("button", { name: "Más acciones: Conjunto norte" }));
    await userEvent.click(await screen.findByRole("menuitem", { name: "Eliminar" }));
    const dialog = await screen.findByRole("alertdialog");
    expect(within(dialog).getByText("Eliminar «Conjunto norte»")).toBeInTheDocument();
    await userEvent.click(within(dialog).getByRole("button", { name: "Eliminar proyecto" }));
    await screen.findByText("Proyecto eliminado").catch(() => undefined);
    expect(screen.queryByRole("link", { name: "Conjunto norte" })).not.toBeInTheDocument();
  });

  it("renames and duplicates", async () => {
    signInAs();
    renderApp("/projects");
    await userEvent.click(await screen.findByRole("button", { name: "Más acciones: Conjunto norte" }));
    await userEvent.click(await screen.findByRole("menuitem", { name: "Duplicar" }));
    expect(await screen.findByRole("link", { name: "Copia de Conjunto norte" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Más acciones: Conjunto norte" }));
    await userEvent.click(await screen.findByRole("menuitem", { name: "Renombrar" }));
    const input = await screen.findByLabelText("Nombre del proyecto");
    await userEvent.clear(input);
    await userEvent.type(input, "Conjunto sur{Enter}");
    expect(await screen.findByRole("link", { name: "Conjunto sur" })).toBeInTheDocument();
  });
});
