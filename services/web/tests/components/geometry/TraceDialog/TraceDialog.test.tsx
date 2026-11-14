import { fireEvent, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { useGeometryStore } from "@/stores/geometry/geometry.store";
import { useNodeFormData } from "../../../utils/form-data-env";
import { renderApp, signInAs } from "../../../utils/render-app";

const P2 = "00000000-0000-4000-8000-0000000000p2";

async function openTrace() {
  signInAs();
  useGeometryStore.setState({ projectId: null, tool: "select", view: "plan" });
  renderApp(`/projects/${P2}/geometry`);
  await userEvent.click(await screen.findByRole("button", { name: "Calcar plano" }));
  return screen.findByRole("dialog");
}

describe("TraceDialog (SCR-08)", () => {
  useNodeFormData();
  afterEach(() => vi.restoreAllMocks());

  it("refuses files over 25 MB before uploading and says how to reduce them", async () => {
    const dialog = await openTrace();
    const big = new File(["x"], "plano.pdf");
    Object.defineProperty(big, "size", { value: 30 * 1024 * 1024 });
    await userEvent.upload(within(dialog).getByLabelText("Imagen o PDF"), big);
    expect(within(dialog).getByRole("alert")).toHaveTextContent("el límite es 25 MB");
  });

  it("offers a page picker for a multi-page PDF, calibrates and measures with the ruler", async () => {
    const dialog = await openTrace();
    await userEvent.upload(within(dialog).getByLabelText("Imagen o PDF"), new File(["%PDF"], "plano.pdf"));
    expect(await within(dialog).findByText("Página 1 de 3")).toBeInTheDocument();
    const img = await within(dialog).findByRole("img", { name: "Página 1 del plano subido" });
    const surface = img.parentElement as HTMLElement;
    vi.spyOn(surface, "getBoundingClientRect").mockReturnValue({ left: 0, top: 0, width: 1, height: 1 } as DOMRect);
    fireEvent.click(surface, { clientX: 0, clientY: 0 });
    fireEvent.click(surface, { clientX: 1, clientY: 0 });
    await userEvent.type(within(dialog).getByLabelText("Distancia real"), "20{Enter}");
    await userEvent.click(within(dialog).getByRole("button", { name: "Guardar escala" }));
    expect(await within(dialog).findByText(/Escala: 1 píxel = 20,0000/)).toBeInTheDocument();
    fireEvent.click(surface, { clientX: 0, clientY: 0 });
    fireEvent.click(surface, { clientX: 1, clientY: 0 });
    expect(within(dialog).getByText("Medida: 20,00 m")).toBeInTheDocument();
  });
});
