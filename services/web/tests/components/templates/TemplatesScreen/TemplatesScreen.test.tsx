import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { templatesState } from "../../../msw/templates/templates.handlers";
import { renderApp, signInAs } from "../../../utils/render-app";

const P1 = "00000000-0000-4000-8000-0000000000p1";

describe("TemplatesScreen (SCR-23)", () => {
  it("lists saved templates", async () => {
    signInAs();
    renderApp("/templates");
    expect(await screen.findByRole("cell", { name: "Centro urbano denso" })).toBeInTheDocument();
  });

  it("invites to save the first template when there are none", async () => {
    templatesState.templates = [];
    signInAs();
    renderApp("/templates");
    expect(await screen.findByRole("heading", { name: "Guarda tu primera plantilla" })).toBeInTheDocument();
  });

  it("saves thresholds, Lawson, terrain and facade defaults but never the location", async () => {
    signInAs();
    renderApp("/templates");
    await userEvent.type(await screen.findByLabelText("Nombre de la plantilla"), "Ladera suburbana");
    await userEvent.click(screen.getByRole("combobox", { name: "Tomar el terreno de" }));
    await userEvent.click(await screen.findByRole("option", { name: "Edificio de la calle 5" }));
    await userEvent.click(screen.getByRole("button", { name: "Guardar plantilla" }));
    expect(await screen.findByRole("cell", { name: "Ladera suburbana" })).toBeInTheDocument();
    const payload = templatesState.created[0].payload;
    expect(payload.thresholds?.k_accel).toBe(1.2);
    expect(payload.lawson?.comfort).toHaveLength(5);
    expect(payload.terrain_category).toBeTruthy();
    expect(payload.facade_defaults).toBeTruthy();
    expect(Object.keys(payload)).not.toEqual(expect.arrayContaining(["lat"]));
    expect(JSON.stringify(payload)).not.toMatch(/"lat"|"lon"|elevation/);
  });

  it("applies a template to a chosen project", async () => {
    signInAs();
    renderApp("/templates");
    await userEvent.click(await screen.findByRole("button", { name: "Aplicar Centro urbano denso" }));
    const dialog = await screen.findByRole("dialog");
    await userEvent.click(within(dialog).getByRole("combobox", { name: "Proyecto" }));
    await userEvent.click(await screen.findByRole("option", { name: "Edificio de la calle 5" }));
    await userEvent.click(within(dialog).getByRole("button", { name: "Aplicar plantilla" }));
    await waitFor(() => expect(templatesState.applied).toEqual([`${P1}:00000000-0000-4000-8000-0000000000t1`]));
  });

  it("deletes a template", async () => {
    signInAs();
    renderApp("/templates");
    await userEvent.click(await screen.findByRole("button", { name: "Eliminar Centro urbano denso" }));
    await waitFor(() => expect(screen.queryByText("Centro urbano denso")).not.toBeInTheDocument());
  });
});
