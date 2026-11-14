import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { useSessionStore } from "@/stores/session/session.store";
import { authState } from "../../../msw/auth/auth.handlers";
import { renderApp } from "../../../utils/render-app";

async function fill(email: string, password: string) {
  await userEvent.type(await screen.findByLabelText("Correo"), email);
  await userEvent.type(screen.getByLabelText("Contraseña"), password);
  await userEvent.click(screen.getByRole("button", { name: "Crear cuenta" }));
}

describe("SetupScreen (SCR-01)", () => {
  it("states the 10-character minimum before typing", async () => {
    authState.needsSetup = true;
    renderApp("/setup");
    expect(await screen.findByText("Mínimo 10 caracteres.")).toBeInTheDocument();
  });

  it("blocks a short password inline without calling the API", async () => {
    authState.needsSetup = true;
    renderApp("/setup");
    await fill("ana@estudio.co", "corta");
    expect(screen.getByText("Usa al menos 10 caracteres.")).toBeInTheDocument();
    expect(authState.needsSetup).toBe(true);
  });

  it("creates the account and lands on an empty project list", async () => {
    authState.needsSetup = true;
    const { projectsState } = await import("../../../msw/projects/projects.handlers");
    projectsState.projects = [];
    const { router } = renderApp("/setup");
    await fill("ana@estudio.co", "contrasena-segura");
    expect(await screen.findByRole("heading", { name: "Crea tu primer proyecto" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/projects");
    expect(useSessionStore.getState().token).not.toBeNull();
  });
});
