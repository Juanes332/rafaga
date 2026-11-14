import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { renderApp } from "../../../utils/render-app";

async function login(password: string) {
  await userEvent.type(await screen.findByLabelText("Correo"), "ana@estudio.co");
  await userEvent.type(screen.getByLabelText("Contraseña"), password);
  await userEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));
}

describe("LoginScreen (SCR-02)", () => {
  it("shows one message for wrong credentials", async () => {
    renderApp("/login");
    await login("incorrecta");
    expect(await screen.findByRole("alert")).toHaveTextContent("Correo o contraseña incorrectos");
  });

  it("shows the wait time from Retry-After on 429", async () => {
    renderApp("/login");
    await login("demasiados");
    expect(await screen.findByRole("alert")).toHaveTextContent("Espera 37 s");
  });

  it("signs in and opens Proyectos", async () => {
    const { router } = renderApp("/login");
    await login("contrasena-segura");
    expect(await screen.findByRole("heading", { name: "Proyectos" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/projects");
  });
});
