import { useMemo } from "react";
import { ExtrudeGeometry, Shape, Vector2 } from "three";
import type { MeshSpec } from "./Geometry3DView.utils";

/** Theme colours read once from CSS tokens; WebGL cannot use var(). */
export function useThemeColors() {
  return useMemo(() => {
    const css = getComputedStyle(document.documentElement);
    const v = (name: string, fallback: string) => css.getPropertyValue(name).trim() || fallback;
    return {
      ground: v("--color-ground", "#e8eceb"),
      building: v("--color-surface-raised", "#fbfcfc"),
      edge: v("--color-ink", "#1e2a30"),
      element: v("--color-ink-muted", "#4c5b62"),
      porous: v("--color-accent", "#2b4fd8"),
      rule: v("--color-rule", "#c5cdcb"),
    };
  }, []);
}

/** Extruded prism: shape in ENU x/y, extruded along +z, then rotated so z is up. */
export function usePrismGeometry(spec: MeshSpec): ExtrudeGeometry {
  return useMemo(() => {
    const shape = new Shape(spec.ring.map(([x, y]) => new Vector2(x, y)));
    return new ExtrudeGeometry(shape, { depth: Math.max(0.05, spec.zMax - spec.zMin), bevelEnabled: false });
  }, [spec.ring, spec.zMax, spec.zMin]);
}
