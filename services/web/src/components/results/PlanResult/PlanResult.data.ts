import { useCallback, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { fieldQueryOptions } from "@/api/results/results.queries";
import { LAWSON_COLORS, kColor, lutIndex, lutRgb, SPEED_LUT, type Rgb } from "@/engines/colormaps/colormap";
import type { Field } from "@/engines/fields/field.decode";
import { buildVelocityData, type VelocityData } from "@/engines/particles/particles.math";
import { computeStreamlines } from "@/engines/streamlines/streamlines";
import type { ResultLayer } from "@/stores/results/results.store";

export interface PlanData {
  K: Field | undefined;
  speed: Field | null;
  paint: Field | undefined;
  paintColor: (v: number) => Rgb;
  speedMax: number;
  velocity: VelocityData | null;
  streamlines: () => number[][];
  isLoading: boolean;
  error: unknown;
}

const TRANSPARENT: Rgb = [0, 0, 0];

function maxFinite(f: Field | undefined): number {
  let m = 0;
  if (f) for (const v of f.data) if (Number.isFinite(v) && v > m) m = v;
  return m;
}

/** Lawson classes as floats with NaN for solids (255) so they stay transparent. */
function lawsonFloat(f: Field | undefined): Field | undefined {
  if (!f) return undefined;
  const data = Float32Array.from(f.data, (v) => (v > 4 ? Number.NaN : v));
  return { ...f, dtype: "float32", data };
}

/** Fields of a plan result for the current layer, plus particle and streamline inputs. */
export function usePlanData(resultId: string, layer: ResultLayer): PlanData {
  const K = useQuery(fieldQueryOptions(resultId, "K"));
  const ux = useQuery(fieldQueryOptions(resultId, "ux"));
  const uy = useQuery(fieldQueryOptions(resultId, "uy"));
  const speed = useQuery({ ...fieldQueryOptions(resultId, "speed"), retry: false });
  const lawson = useQuery({ ...fieldQueryOptions(resultId, "lawson_class"), enabled: layer === "lawson", retry: false });
  const speedMax = useMemo(() => maxFinite(speed.data), [speed.data]);
  const lawsonField = useMemo(() => lawsonFloat(lawson.data), [lawson.data]);
  const velocity = useMemo(
    () => (K.data && ux.data && uy.data ? buildVelocityData(K.data.data as Float32Array, ux.data.data as Float32Array, uy.data.data as Float32Array, K.data.cols, K.data.rows) : null),
    [K.data, ux.data, uy.data],
  );
  const streamlines = useCallback(() => {
    if (!ux.data || !uy.data) return [];
    const spacing = Math.max(3, Math.round(ux.data.cols / 40));
    return computeStreamlines({ cols: ux.data.cols, rows: ux.data.rows, u: ux.data.data as Float32Array, v: uy.data.data as Float32Array }, spacing);
  }, [ux.data, uy.data]);
  const [paint, paintColor] = useMemo((): [Field | undefined, (v: number) => Rgb] => {
    if (layer === "speed" && speed.data) return [speed.data, (v) => lutRgb(SPEED_LUT, lutIndex(v, [0, Math.max(1, Math.ceil(speedMax))]))];
    if (layer === "lawson" && lawsonField) return [lawsonField, (v) => LAWSON_COLORS[v] ?? TRANSPARENT];
    return [K.data, kColor];
  }, [layer, speed.data, speedMax, lawsonField, K.data]);
  return {
    K: K.data,
    speed: speed.data ?? null,
    paint,
    paintColor,
    speedMax,
    velocity,
    streamlines,
    isLoading: K.isLoading || ux.isLoading || uy.isLoading,
    error: K.error ?? ux.error ?? uy.error,
  };
}
