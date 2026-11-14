import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { useFacadesStore } from "@/stores/facades/facades.store";
import { alternativesState } from "../../../msw/alternatives/alternatives.handlers";
import { renderApp, signInAs } from "../../../utils/render-app";

const P1 = "/projects/00000000-0000-4000-8000-0000000000p1/alternatives";
const P2 = "/projects/00000000-0000-4000-8000-0000000000p2/alternatives";

describe("AlternativesStep (SCR-11)", () => {
  beforeEach(() => useFacadesStore.getState().reset());

  it("opens the first non-base alternative with its strategy listed", async () => {
    signInAs();
    renderApp(P1);
    expect(await screen.findByRole("button", { name: /Celosía 40 %/, pressed: true })).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Celosía porosa en la fachada 2 de Torre A" })).toBeInTheDocument();
  });

  it("marks the base as immutable and not pickable", async () => {
    signInAs();
    renderApp(P1);
    await userEvent.click(await screen.findByRole("button", { name: /^Base/ }));
    expect(screen.getByText(/El caso base son tus edificios sin estrategias/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Fachada 1 de Torre A/ })).not.toBeInTheDocument();
  });

  it("applies a strategy with defaults to a selected façade", async () => {
    signInAs();
    renderApp(P1);
    await userEvent.click(await screen.findByRole("button", { name: /^Fachada 3 de Torre A/ }));
    expect(screen.getByRole("textbox", { name: "Porosidad" })).toHaveValue("40");
    await userEvent.click(screen.getByRole("button", { name: "Aplicar estrategia" }));
    expect(await screen.findByRole("button", { name: "Celosía porosa en la fachada 3 de Torre A" })).toBeInTheDocument();
  });

  it("shows the adjustment message when the api clamps a value", async () => {
    signInAs();
    renderApp(P1);
    await userEvent.click(await screen.findByRole("button", { name: "Celosía porosa en la fachada 2 de Torre A" }));
    const height = screen.getByRole("textbox", { name: "Altura" });
    await userEvent.clear(height);
    await userEvent.type(height, "45{Enter}");
    expect(await screen.findByText(/Se ajustó Altura de 45,0 a 36,0/)).toBeInTheDocument();
  });

  it("explains the alternatives limit on 409", async () => {
    const list = alternativesState.byProject["00000000-0000-4000-8000-0000000000p1"];
    for (let i = 0; i < 6; i += 1) list.push({ ...list[1], id: `x${i}`, name: `Alt ${i}` });
    signInAs();
    renderApp(P1);
    await userEvent.click(await screen.findByRole("button", { name: "Crear alternativa" }));
    const dialog = await screen.findByRole("dialog");
    await userEvent.type(within(dialog).getByLabelText("Nombre de la alternativa"), "Aletas");
    await userEvent.click(within(dialog).getByRole("button", { name: "Crear alternativa" }));
    expect(await within(dialog).findByRole("alert")).toHaveTextContent("Llegaste al límite de 8 alternativas");
  });

  it("creates an alternative and opens it", async () => {
    signInAs();
    renderApp(P1);
    await userEvent.click(await screen.findByRole("button", { name: "Crear alternativa" }));
    await userEvent.type(await screen.findByLabelText("Nombre de la alternativa"), "Aletas 1 m{Enter}");
    expect(await screen.findByRole("button", { name: /Aletas 1 m/, pressed: true })).toBeInTheDocument();
  });

  it("asks for buildings first on a project without geometry", async () => {
    signInAs();
    renderApp(P2);
    expect(await screen.findByRole("heading", { name: "Dibuja o carga tu primer edificio" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Crea una alternativa para probar una estrategia de fachada" })).toBeInTheDocument();
  });
});
