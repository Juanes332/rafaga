import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useGeolocation } from "@/hooks/geolocation/use-geolocation";

type Success = (p: GeolocationPosition) => void;
type Failure = (e: GeolocationPositionError) => void;

function stubGeolocation(impl: (ok: Success, fail: Failure, opts?: PositionOptions) => void) {
  const getCurrentPosition = vi.fn(impl);
  Object.defineProperty(navigator, "geolocation", { value: { getCurrentPosition }, configurable: true });
  return getCurrentPosition;
}

function fix(lat: number, lon: number, accuracy: number): GeolocationPosition {
  return { coords: { latitude: lat, longitude: lon, accuracy } } as GeolocationPosition;
}

function failure(code: number): GeolocationPositionError {
  return { code, PERMISSION_DENIED: 1, POSITION_UNAVAILABLE: 2, TIMEOUT: 3, message: "" } as GeolocationPositionError;
}

describe("useGeolocation", () => {
  beforeEach(() => {
    Object.defineProperty(window, "isSecureContext", { value: true, configurable: true });
  });
  afterEach(() => {
    Reflect.deleteProperty(navigator, "geolocation");
  });

  it("asks for a high-accuracy fix with a timeout and reports position and accuracy", () => {
    const get = stubGeolocation((ok) => ok(fix(5.5369, -73.3606, 12.4)));
    const onFix = vi.fn();
    const { result } = renderHook(() => useGeolocation(onFix));
    act(() => result.current.locate());
    expect(get.mock.calls[0][2]).toMatchObject({ enableHighAccuracy: true, timeout: expect.any(Number), maximumAge: 0 });
    expect(onFix).toHaveBeenCalledWith({ lat: 5.5369, lon: -73.3606, accuracyM: 12.4 });
    expect(result.current.status).toBe("success");
    expect(result.current.accuracyM).toBe(12.4);
  });

  it("is locating until the browser answers", () => {
    stubGeolocation(() => undefined);
    const { result } = renderHook(() => useGeolocation(vi.fn()));
    act(() => result.current.locate());
    expect(result.current.status).toBe("locating");
  });

  it.each([
    [1, "denied"],
    [2, "unavailable"],
    [3, "timeout"],
  ])("maps error code %i to %s", (code, kind) => {
    stubGeolocation((_ok, fail) => fail(failure(code)));
    const onFix = vi.fn();
    const { result } = renderHook(() => useGeolocation(onFix));
    act(() => result.current.locate());
    expect(result.current.status).toBe("error");
    expect(result.current.error).toBe(kind);
    expect(onFix).not.toHaveBeenCalled();
  });

  it("does not call the browser in an insecure context", () => {
    Object.defineProperty(window, "isSecureContext", { value: false, configurable: true });
    const get = stubGeolocation(() => undefined);
    const { result } = renderHook(() => useGeolocation(vi.fn()));
    act(() => result.current.locate());
    expect(get).not.toHaveBeenCalled();
    expect(result.current.error).toBe("insecure");
  });

  it("reports unsupported when the browser has no geolocation", () => {
    const { result } = renderHook(() => useGeolocation(vi.fn()));
    act(() => result.current.locate());
    expect(result.current.error).toBe("unsupported");
  });
});
