import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { sceneQueryOptions } from "@/api/scene/scene.queries";
import { toMeshSpecs, type MeshSpec } from "@/components/geometry/Geometry3DView/Geometry3DView.utils";
import { useGeometryStore } from "@/stores/geometry/geometry.store";

/** Mesh specs for the 3D view: draft buildings + the alternative's compiled elements. */
export function useGeometry3DData(alternativeId: string | null): MeshSpec[] {
  const buildings = useGeometryStore((s) => s.buildings);
  const scene = useQuery({ ...sceneQueryOptions(alternativeId ?? ""), enabled: Boolean(alternativeId) });
  return useMemo(() => toMeshSpecs(buildings, scene.data), [buildings, scene.data]);
}
