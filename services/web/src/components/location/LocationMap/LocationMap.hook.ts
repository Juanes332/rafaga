import { useEffect, useRef, useState, type RefObject } from "react";
import { useTranslation } from "react-i18next";
import { createMap, supportsWebGL, type MapAdapter } from "./LocationMap.adapter";
import type { LocationMapProps, MapStatus } from "./LocationMap.types";

interface UseLocationMap {
  container: RefObject<HTMLDivElement | null>;
  status: MapStatus;
}

/** Owns the MapLibre lifecycle; the marker only appears once a location exists. */
export function useLocationMap({ lat, lon, onPick }: LocationMapProps): UseLocationMap {
  const { t } = useTranslation();
  const container = useRef<HTMLDivElement>(null);
  const adapter = useRef<MapAdapter | null>(null);
  const pick = useRef(onPick);
  pick.current = onPick;
  const [status, setStatus] = useState<MapStatus>(() => (supportsWebGL() ? "loading" : "unsupported"));
  const initial = useRef<[number, number] | null>(lat != null && lon != null ? [lon, lat] : null);

  useEffect(() => {
    if (status === "unsupported" || !container.current) return;
    let alive = true;
    void createMap(container.current, initial.current, {
      onPick: (a, b) => pick.current(a, b),
      onOffline: () => alive && setStatus("offline"),
    })
      .then((m) => (alive ? ((adapter.current = m), setStatus((s) => (s === "offline" ? s : "ready"))) : m.remove()))
      .catch(() => alive && setStatus("unsupported"));
    return () => {
      alive = false;
      adapter.current?.remove();
      adapter.current = null;
    };
    // The map is created once; later location changes only move the marker.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (lat != null && lon != null && adapter.current) adapter.current.setMarker(lat, lon, t("location:map.marker"));
  }, [lat, lon, status, t]);

  return { container, status };
}
