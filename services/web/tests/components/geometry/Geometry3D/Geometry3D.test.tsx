import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Geometry3D } from "@/components/geometry/Geometry3D/Geometry3D";
import { renderWithProviders } from "../../../utils/render-with-providers";

vi.mock("@/components/geometry/Geometry3DView/Geometry3DView", () => ({
  Geometry3DView: ({ label }: { label: string }) => <div role="img" aria-label={label} />,
}));

describe("Geometry3D (SCR-09)", () => {
  afterEach(() => vi.restoreAllMocks());

  it("shows a loading fallback while three.js loads, then the view", async () => {
    vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({} as RenderingContext);
    renderWithProviders(<Geometry3D projectId="00000000-0000-4000-8000-0000000000p1" />);
    expect(screen.getByText("Cargando vista 3D")).toBeInTheDocument();
    expect(await screen.findByRole("img", { name: /Vista 3D de la geometría/ })).toBeInTheDocument();
    expect(await screen.findByLabelText("Alternativa")).toBeInTheDocument();
  });
});
