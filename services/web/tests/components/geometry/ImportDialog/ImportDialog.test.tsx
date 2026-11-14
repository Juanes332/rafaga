import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { useGeometryStore } from "@/stores/geometry/geometry.store";
import { useNodeFormData } from "../../../utils/form-data-env";
import { renderApp, signInAs } from "../../../utils/render-app";

const P1 = "00000000-0000-4000-8000-0000000000p1";
const P2 = "00000000-0000-4000-8000-0000000000p2";

async function importFile(projectId: string, name: string) {
  signInAs();
  useGeometryStore.setState({ projectId: null, tool: "select", view: "plan" });
  renderApp(`/projects/${projectId}/geometry`);
  await userEvent.click((await screen.findAllByRole("button", { name: "Importar archivo" }))[0]);
  const dialog = await screen.findByRole("dialog");
  await userEvent.upload(within(dialog).getByLabelText("Archivo"), new File(["0"], name));
  await userEvent.click(within(dialog).getByRole("button", { name: "Importar" }));
  return dialog;
}

describe("ImportDialog (SCR-07)", () => {
  useNodeFormData();

  it("reports added buildings, the detected unit and ignored entities", async () => {
    const dialog = await importFile(P2, "plano.dxf");
    expect(await within(dialog).findByText(/2 edificios añadidos\. Unidad detectada: centímetros\./)).toBeInTheDocument();
    expect(within(dialog).getByText("La polilínea no está cerrada.")).toBeInTheDocument();
  });

  it("asks for missing heights inline and applies them", async () => {
    const dialog = await importFile(P2, "plano.dxf");
    const input = await within(dialog).findByLabelText("Importado 2");
    await userEvent.type(input, "9{Enter}");
    await userEvent.click(within(dialog).getByRole("button", { name: "Aplicar alturas" }));
    const b = useGeometryStore.getState().buildings.find((x) => x.name === "Importado 2");
    expect(b?.height_m).toBe(9);
  });

  it("explains a failed import with cause and fix", async () => {
    const dialog = await importFile(P2, "falla.dxf");
    expect(await within(dialog).findByRole("alert")).toHaveTextContent("Cierra los contornos de los edificios");
  });

  it("explains that imports are blocked while alternatives exist", async () => {
    const dialog = await importFile(P1, "plano.dxf");
    expect(await within(dialog).findByRole("alert")).toHaveTextContent("No se puede importar geometría mientras haya alternativas");
  });
});
