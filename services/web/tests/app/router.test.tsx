import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { authState } from "../msw/auth/auth.handlers";
import { renderApp, signInAs } from "../utils/render-app";

describe("route gate", () => {
  it("shows account creation on any route while setup is needed", async () => {
    authState.needsSetup = true;
    const { router } = renderApp("/projects/x/wind");
    expect(await screen.findByRole("heading", { name: "Crea tu cuenta local" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/setup");
  });

  it("sends a visitor without a session to login", async () => {
    renderApp("/projects");
    expect(await screen.findByRole("heading", { name: "Inicia sesión" })).toBeInTheDocument();
  });

  it("lands a signed-in user on Proyectos from /", async () => {
    signInAs();
    const { router } = renderApp("/");
    expect(await screen.findByRole("heading", { name: "Proyectos" })).toBeInTheDocument();
    await waitFor(() => expect(router.state.location.pathname).toBe("/projects"));
  });

  it("opens a project on its first step", async () => {
    signInAs();
    const { router } = renderApp("/projects/00000000-0000-4000-8000-0000000000p1");
    await waitFor(() => expect(router.state.location.pathname).toMatch(/\/location$/));
    expect(await screen.findByRole("navigation", { name: "Pasos del proyecto" })).toBeInTheDocument();
  });
});
