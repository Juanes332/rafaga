import { useCallback, useRef, useState } from "react";

export type GeolocationErrorKind = "denied" | "unavailable" | "timeout" | "insecure" | "unsupported";

export interface GeoFix {
  lat: number;
  lon: number;
  accuracyM: number;
}

export interface UseGeolocation {
  status: "idle" | "locating" | "success" | "error";
  accuracyM: number | null;
  error: GeolocationErrorKind | null;
  locate: () => void;
}

const OPTIONS: PositionOptions = { enableHighAccuracy: true, timeout: 15_000, maximumAge: 0 };
const BY_CODE: Record<number, GeolocationErrorKind> = { 1: "denied", 2: "unavailable", 3: "timeout" };

/** One-shot device position; coordinates stay in the browser and go only to onFix. */
export function useGeolocation(onFix: (fix: GeoFix) => void): UseGeolocation {
  const [state, setState] = useState<Omit<UseGeolocation, "locate">>({ status: "idle", accuracyM: null, error: null });
  const handler = useRef(onFix);
  handler.current = onFix;

  const fail = (error: GeolocationErrorKind) => setState({ status: "error", accuracyM: null, error });

  const locate = useCallback(() => {
    // Browsers only expose GPS on https or localhost; a LAN http IP fails silently otherwise.
    if (!window.isSecureContext) return fail("insecure");
    if (!navigator.geolocation) return fail("unsupported");
    setState({ status: "locating", accuracyM: null, error: null });
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        setState({ status: "success", accuracyM: coords.accuracy, error: null });
        handler.current({ lat: coords.latitude, lon: coords.longitude, accuracyM: coords.accuracy });
      },
      (e) => fail(BY_CODE[e.code] ?? "unavailable"),
      OPTIONS,
    );
  }, []);

  return { ...state, locate };
}
