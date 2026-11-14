import { screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { authState } from "../msw/auth/auth.handlers";
import { seriousViolations } from "../utils/axe";
import { renderApp, signInAs } from "../utils/render-app";

describe("accessibility (axe, structural rules)", () => {
  it.each(["light", "dark"])("account creation has no serious violations (%s)", async (theme) => {
    document.documentElement.setAttribute("data-theme", theme);
    authState.needsSetup = true;
    renderApp("/setup");
    await screen.findByRole("heading", { name: "Crea tu cuenta local" });
    expect(await seriousViolations()).toEqual([]);
  });

  it("login has no serious violations", async () => {
    renderApp("/login");
    await screen.findByRole("heading", { name: "Inicia sesión" });
    expect(await seriousViolations()).toEqual([]);
  });

  it("projects list has no serious violations", async () => {
    signInAs();
    renderApp("/projects");
    await screen.findByRole("link", { name: "Conjunto norte" });
    expect(await seriousViolations()).toEqual([]);
  });
});
