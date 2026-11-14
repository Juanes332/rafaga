import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { ApiError } from "@/lib/http/api-error";

describe("ErrorNotice", () => {
  it("shows the cause and fix for an API error code", () => {
    render(<ErrorNotice error={new ApiError(503, "era5_unavailable", "x")} />);
    expect(screen.getByRole("alert")).toHaveTextContent(/no hay conexión y este sitio no está en caché/);
  });

  it("runs the recovery action", async () => {
    const onAction = vi.fn();
    render(<ErrorNotice message="Falló." actionLabel="Reintentar" onAction={onAction} />);
    await userEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(onAction).toHaveBeenCalled();
  });
});
