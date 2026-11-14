import { useMemo } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import { fieldQueryOptions, viewer3dQueryOptions, type FieldName } from "@/api/results/results.queries";
import type { Field } from "@/engines/fields/field.decode";
import type { Viewer3D } from "@/types/results/result.types";
import { cameraFor, fieldMax, type Bounds } from "./ResultsViewer3D.utils";

export interface SliceData {
  name: string;
  plane: "xy" | "xz" | "yz";
  extents: number[];
  field: Field;
}

export interface Solid {
  id: string;
  footprint: number[][];
  z_min: number;
  z_max: number;
}

/** viewer3d payload + its slice fields, ready for the scene. */
export function useResultsViewer3D(resultId: string) {
  const viewer = useQuery(viewer3dQueryOptions(resultId));
  const slices: Viewer3D["slices"] = viewer.data?.slices ?? [];
  const fields = useQueries({ queries: slices.map((s) => fieldQueryOptions(resultId, s.field as FieldName)) });
  const sliceData: SliceData[] = slices.flatMap((s, i) => {
    const f = fields[i]?.data;
    return f ? [{ name: s.name, plane: s.plane, extents: s.extents, field: f }] : [];
  });
  const scene = viewer.data?.scene as unknown as { solids?: Solid[]; bounds?: { base_min: number[]; base_max: number[] } } | undefined;
  const bounds: Bounds = {
    min: (scene?.bounds?.base_min ?? [0, 0, 0]) as Bounds["min"],
    max: (scene?.bounds?.base_max ?? [50, 50, 30]) as Bounds["max"],
  };
  const max = useMemo(() => fieldMax(sliceData.map((s) => s.field)), [sliceData]);
  return {
    isLoading: viewer.isLoading,
    error: viewer.error,
    solids: scene?.solids ?? [],
    slices: sliceData,
    streamlines: viewer.data?.streamlines ?? [],
    bounds,
    camera: cameraFor(bounds),
    max,
  };
}
