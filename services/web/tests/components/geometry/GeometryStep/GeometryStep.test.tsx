import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { useGeometryStore } from "@/stores/geometry/geometry.store";
import { geometryOf, P1 } from "../../../msw/geometry/geometry.handlers";
import { renderApp, signInAs } from "../../../utils/render-app";

const P2 = "00000000-0000-4000-8000-0000000000p2";
const open = async (projectId: string, role: "architect" | "reviewer" = "architect") => {
  signInAs(role);
  useGeometryStore.setState({ projectId: null, tool: "select", view: "plan" });
  const r = renderApp(`/projects/${projectId}/geometry`);
  await screen.findByRole("application", { name: /Planta de edificios/ });
  return r;
};

describe("GeometryStep (SCR-06)", () => {
  it("draws the saved buildings as focusable blocks with their height", async () => {
    await open(P1);
    expect(await screen.findByRole("button", { name: /^Torre A 36,0\s?m$/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Bloque B 18,0\s?m$/ })).toHaveAttribute("tabindex", "0");
  });

  it("invites to draw or import when there are no buildings", async () => {
    await open(P2);
    expect(await screen.findByRole("heading", { name: "Dibuja o carga tu primer edificio" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Dibujar bloque" }));
    expect(useGeometryStore.getState().tool).toBe("rect");
    expect(screen.getByRole("radio", { name: "Rectángulo" })).toHaveAttribute("aria-checked", "true");
  });

  it("edits the selected building's height and saves after confirming the base change", async () => {
    await open(P1);
    await userEvent.click(await screen.findByRole("button", { name: /Torre A/ }));
    // The slider thumb shares the label; the text field is the <input>.
    const height = (await screen.findAllByLabelText("Altura")).find((el) => el.tagName === "INPUT") as HTMLInputElement;
    await userEvent.clear(height);
    await userEvent.type(height, "42{Enter}");
    expect(screen.getByText("Cambios sin guardar")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    const dialog = await screen.findByRole("alertdialog");
    await userEvent.click(within(dialog).getByRole("button", { name: "Guardar y actualizar alternativas" }));
    await waitFor(() => expect(geometryOf(P1).version).toBe(4));
    expect(geometryOf(P1).buildings[0].height_m).toBe(42);
  });

  it("deletes with the keyboard and restores with Ctrl+Z", async () => {
    await open(P1);
    const block = await screen.findByRole("button", { name: /Bloque B/ });
    block.focus();
    await userEvent.keyboard("{Delete}");
    expect(screen.queryByRole("button", { name: /Bloque B/ })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Deshacer" }));
    expect(await screen.findByRole("button", { name: /Bloque B/ })).toBeInTheDocument();
    await userEvent.keyboard("{Control>}{Shift>}z{/Shift}{/Control}");
    expect(useGeometryStore.getState().buildings).toHaveLength(1);
  });

  it("nudges a block with the arrow keys", async () => {
    await open(P1);
    (await screen.findByRole("button", { name: /Torre A/ })).focus();
    await userEvent.keyboard("{ArrowRight}");
    expect(useGeometryStore.getState().buildings[0].footprint[0]).toEqual([1, 0]);
  });

  it("lists server validation issues", async () => {
    await open(P1);
    useGeometryStore.setState((s) => ({ buildings: s.buildings.map((b, i) => (i === 0 ? { ...b, height_m: 900 } : b)) }));
    await userEvent.click(await screen.findByRole("button", { name: "Comprobar geometría" }));
    expect(await screen.findByText("La altura está fuera de rango. Usa un valor entre 1 y 500 m.")).toBeInTheDocument();
  });

  it("hides editing tools for reviewers", async () => {
    await open(P1, "reviewer");
    expect(screen.queryByRole("button", { name: "Guardar cambios" })).not.toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "Herramientas" })).not.toBeInTheDocument();
  });

  it("switches to the 3D view and explains when WebGL is missing", async () => {
    await open(P1);
    await userEvent.click(screen.getByRole("radio", { name: "3D" }));
    expect(await screen.findByText(/WebGL no disponible/)).toBeInTheDocument();
  });
});
