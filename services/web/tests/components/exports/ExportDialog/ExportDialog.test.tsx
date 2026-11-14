import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ExportDialog } from "@/components/exports/ExportDialog/ExportDialog";
import { exportsState } from "../../../msw/exports/exports.handlers";
import { renderWithProviders } from "../../../utils/render-with-providers";

const R1 = "00000000-0000-4000-8000-0000000000r1";

describe("ExportDialog (SCR-19)", () => {
  afterEach(() => vi.restoreAllMocks());

  it("is disabled with an explanation when the view has no results", () => {
    renderWithProviders(<ExportDialog open resultId={null} onOpenChange={vi.fn()} />);
    expect(screen.getByText(/No hay resultados en esta vista/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Exportar PNG" })).toBeDisabled();
  });

  it("offers ΔK only when comparing two results", () => {
    const { unmount } = renderWithProviders(<ExportDialog open resultId={R1} onOpenChange={vi.fn()} />);
    expect(screen.queryByRole("radio", { name: /ΔK/ })).not.toBeInTheDocument();
    unmount();
    renderWithProviders(<ExportDialog open resultId={R1} compareResultId="r2" onOpenChange={vi.fn()} />);
    expect(screen.getByRole("radio", { name: /ΔK/ })).toBeInTheDocument();
  });

  it("exports with current thresholds, polls until ready and saves the PNG", async () => {
    const createUrl = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:png");
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    renderWithProviders(<ExportDialog open resultId={R1} onOpenChange={vi.fn()} />);
    await userEvent.click(screen.getByRole("radio", { name: "Zonas" }));
    await userEvent.click(screen.getByRole("radio", { name: "600 ppp" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Exportar PNG" })).toBeEnabled());
    await userEvent.click(screen.getByRole("button", { name: "Exportar PNG" }));
    expect(await screen.findByRole("button", { name: "Exportando PNG" })).toBeDisabled();
    expect(await screen.findByText("PNG listo para descargar", {}, { timeout: 4000 })).toBeInTheDocument();
    expect(exportsState.requests[0]).toMatchObject({
      result_id: R1,
      layer: "zones",
      dpi: 600,
      thresholds: { k_accel: 1.2, k_stagnation: 0.3, dk_reduction: -0.1 },
    });
    await waitFor(() => expect(createUrl).toHaveBeenCalled());
  });
});
