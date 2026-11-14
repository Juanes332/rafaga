import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Disclaimer } from "@/components/feedback/Disclaimer/Disclaimer";

describe("Disclaimer", () => {
  it("shows the exact FR-48 text", () => {
    render(<Disclaimer />);
    expect(screen.getByText("Herramienta de anteproyecto: compara alternativas, no sustituye un ensayo en túnel de viento.")).toBeInTheDocument();
  });

  it("merges a non-alarming model-confidence note as expandable detail", async () => {
    render(<Disclaimer />);
    const note = screen.getByText(/^Ráfaga sirve para comparar alternativas y detectar zonas incómodas en etapas de diseño\. No reemplaza un ensayo en túnel de viento para proyectos críticos\.$/);
    expect(note.closest("details")).not.toBeNull();
    expect(screen.getByText("¿Qué tan fiable es?")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
