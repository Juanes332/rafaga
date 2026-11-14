import type { Map as MapLibreMap, Marker, StyleSpecification } from "maplibre-gl";
import { authHeaders, getApiBase } from "@/lib/http/api-client";

/** The slice of MapLibre the step needs; keeps WebGL out of component logic and tests. */
export interface MapAdapter {
  setMarker: (lat: number, lon: number, label: string) => void;
  remove: () => void;
}

interface MapEvents {
  onPick: (lat: number, lon: number) => void;
  onOffline: () => void;
}

export const ATTRIBUTION = "© OpenStreetMap contributors";

/** WebGL availability without touching jsdom's unimplemented canvas. */
export function supportsWebGL(): boolean {
  if (typeof window === "undefined" || (!("WebGL2RenderingContext" in window) && !("WebGLRenderingContext" in window))) return false;
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") ?? canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

/** Raster OSM tiles through the authenticated api proxy (ADR-09); no background layer so the offline grid shows. */
export function rasterStyle(apiBase: string): StyleSpecification {
  return {
    version: 8,
    sources: {
      osm: { type: "raster", tiles: [`${apiBase}/tiles/{z}/{x}/{y}.png`], tileSize: 256, maxzoom: 19, attribution: ATTRIBUTION },
    },
    layers: [{ id: "osm", type: "raster", source: "osm" }],
  };
}

function markerElement(label: string): HTMLElement {
  const el = document.createElement("div");
  el.className = "rafaga-site-marker";
  el.setAttribute("role", "img");
  el.setAttribute("aria-label", label);
  return el;
}

/** Lazy-load MapLibre and build the map; a new project starts on a neutral world view. */
export async function createMap(container: HTMLElement, center: [number, number] | null, events: MapEvents): Promise<MapAdapter> {
  const maplibre = await import("maplibre-gl");
  await import("maplibre-gl/dist/maplibre-gl.css");
  const base = getApiBase();
  const map: MapLibreMap = new maplibre.Map({
    container,
    style: rasterStyle(base),
    center: center ?? [0, 20],
    zoom: center ? 15 : 1.5,
    attributionControl: { compact: false },
    transformRequest: (url) => (url.startsWith(base) ? { url, headers: authHeaders() } : { url }),
  });
  map.addControl(new maplibre.NavigationControl({ showCompass: false }), "top-right");
  map.on("click", (e) => events.onPick(e.lngLat.lat, e.lngLat.lng));
  map.on("error", (e) => ("sourceId" in e && e.sourceId === "osm" ? events.onOffline() : undefined));
  let marker: Marker | null = null;
  return {
    setMarker: (lat, lon, label) => {
      marker ??= new maplibre.Marker({ element: markerElement(label) }).setLngLat([lon, lat]).addTo(map);
      marker.setLngLat([lon, lat]);
      map.flyTo({ center: [lon, lat], zoom: Math.max(map.getZoom(), 15), duration: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 600 });
    },
    remove: () => map.remove(),
  };
}
