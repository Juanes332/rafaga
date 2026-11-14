import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { usersState } from "../../../msw/users/users.handlers";
import { renderApp, signInAs } from "../../../utils/render-app";

const P1_NAME = "Edificio de la calle 5";

describe("UsersScreen (SCR-22)", () => {
  it("lists local users with roles and marks yourself", async () => {
    signInAs();
    renderApp("/users");
    expect(await screen.findByText("ana@estudio.co (tú)")).toBeInTheDocument();
    const row = screen.getByText("rev@estudio.co").closest("tr") as HTMLElement;
    expect(within(row).getByText("Revisor")).toBeInTheDocument();
  });

  it("creates a reviewer account", async () => {
    signInAs();
    renderApp("/users");
    await userEvent.type(await screen.findByLabelText("Correo"), "admin@rafaga.local");
    await userEvent.type(screen.getByLabelText("Contraseña inicial"), "0123456789");
    await userEvent.click(screen.getByRole("radio", { name: "Revisor" }));
    await userEvent.click(screen.getByRole("button", { name: "Crear usuario" }));
    expect(await screen.findByText("admin@rafaga.local")).toBeInTheDocument();
    expect(usersState.users.at(-1)?.role).toBe("reviewer");
  });

  it("explains a short password before sending", async () => {
    signInAs();
    renderApp("/users");
    await userEvent.type(await screen.findByLabelText("Correo"), "x@y.co");
    await userEvent.type(screen.getByLabelText("Contraseña inicial"), "corta");
    await userEvent.click(screen.getByRole("button", { name: "Crear usuario" }));
    expect(screen.getByText("Usa al menos 10 caracteres.")).toBeInTheDocument();
  });

  it("deletes another user after confirmation", async () => {
    signInAs();
    renderApp("/users");
    await userEvent.click(await screen.findByRole("button", { name: "Eliminar a rev@estudio.co" }));
    const dialog = await screen.findByRole("alertdialog");
    await userEvent.click(within(dialog).getByRole("button", { name: "Eliminar usuario" }));
    await waitFor(() => expect(screen.queryByText("rev@estudio.co")).not.toBeInTheDocument());
  });

  it("revokes and grants project access", async () => {
    signInAs();
    renderApp("/users");
    await userEvent.click(await screen.findByRole("combobox", { name: "Proyecto" }));
    await userEvent.click(await screen.findByRole("option", { name: P1_NAME }));
    const toggle = await screen.findByRole("switch", { name: "Dar acceso a rev@estudio.co" });
    await waitFor(() => expect(toggle).toBeChecked());
    await userEvent.click(toggle);
    await waitFor(() => expect(usersState.shares["00000000-0000-4000-8000-0000000000p1"]).toHaveLength(0));
    await waitFor(() => expect(screen.getByRole("switch", { name: "Dar acceso a rev@estudio.co" })).not.toBeChecked());
  });

  it("explains to a reviewer that only architects manage access", async () => {
    signInAs("reviewer");
    renderApp("/users");
    expect(await screen.findByText(/Solo un arquitecto puede gestionar usuarios y accesos/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Crear usuario" })).not.toBeInTheDocument();
  });

  it("shows a reviewer the read-only banner inside a project", async () => {
    signInAs("reviewer");
    renderApp("/projects/00000000-0000-4000-8000-0000000000p1/location");
    expect(await screen.findByText(/Solo lectura: este proyecto está compartido contigo/)).toBeInTheDocument();
  });
});
