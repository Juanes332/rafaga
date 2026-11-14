import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GpsButton } from "@/components/location/GpsButton/GpsButton";

function stub(impl: (ok: PositionCallback, fail: PositionErrorCallback) => void) {
  Object.defineProperty(navigator, "geolocation", { value: { getCurrentPosition: impl }, configurable: true });
}

describe("GpsButton", () => {
  beforeEach(() => {
    Object.defineProperty(window, "isSecureContext", { value: true, configurable: true });
  });
  afterEach(() => {
    Reflect.deleteProperty(navigator, "geolocation");
  });

  it("fixes the location from the device and announces the accuracy in metres", async () => {
    stub((ok) => ok({ coords: { latitude: 5.5369, longitude: -73.3606, accuracy: 12.4 } } as GeolocationPosition));
    const onFix = vi.fn();
    render(<GpsButton disabled={false} onFix={onFix} />);
    await userEvent.click(screen.getByRole("button", { name: "Usar mi ubicación" }));
    expect(onFix).toHaveBeenCalledWith(5.5369, -73.3606);
    expect(screen.getByRole("status")).toHaveTextContent("±12 m");
  });

  it("explains a denied permission and how to continue", async () => {
    stub((_ok, fail) => fail({ code: 1 } as GeolocationPositionError));
    render(<GpsButton disabled={false} onFix={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: "Usar mi ubicación" }));
    expect(screen.getByRole("alert")).toHaveTextContent(/permiso/i);
  });

  it("explains that GPS needs a secure connection when opened by a LAN address", async () => {
    Object.defineProperty(window, "isSecureContext", { value: false, configurable: true });
    render(<GpsButton disabled={false} onFix={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: "Usar mi ubicación" }));
    expect(screen.getByRole("alert")).toHaveTextContent(/https o localhost/);
  });

  it("keeps an empty live region mounted so the first result is announced", () => {
    render(<GpsButton disabled={false} onFix={vi.fn()} />);
    expect(screen.getByRole("status")).toBeEmptyDOMElement();
  });

  it("is disabled for read-only or pending states", () => {
    render(<GpsButton disabled onFix={vi.fn()} />);
    expect(screen.getByRole("button", { name: "Usar mi ubicación" })).toBeDisabled();
  });
});
