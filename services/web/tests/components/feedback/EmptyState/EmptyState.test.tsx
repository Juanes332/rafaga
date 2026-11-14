import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EmptyState } from "@/components/feedback/EmptyState/EmptyState";

describe("EmptyState", () => {
  it("renders the invitation as a heading with its action", () => {
    render(
      <EmptyState title="Crea tu primer proyecto">
        <button>Nuevo proyecto</button>
      </EmptyState>,
    );
    expect(screen.getByRole("heading", { name: "Crea tu primer proyecto" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Nuevo proyecto" })).toBeInTheDocument();
  });
});
