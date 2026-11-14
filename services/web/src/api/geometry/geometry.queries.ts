import { queryOptions, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/http/api-client";
import type { Building, Geometry, GeometryValidation, ImportReport } from "@/types/geometry/geometry.types";

export const geometryKeys = {
  detail: (projectId: string) => ["geometry", projectId] as const,
  backgrounds: (projectId: string) => ["geometry", projectId, "backgrounds"] as const,
};

/** Base buildings of a project (versioned). */
export const geometryQueryOptions = (projectId: string) =>
  queryOptions({
    queryKey: geometryKeys.detail(projectId),
    queryFn: () => apiClient.get<Geometry>(`/projects/${projectId}/geometry`),
  });

export interface SaveGeometryInput {
  expectedVersion: number;
  buildings: Building[];
  confirmBaseChange?: boolean;
}

/** PUT /geometry with optimistic concurrency; 409 version_conflict / base_locked bubble up. */
export function useSaveGeometry(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: SaveGeometryInput) =>
      apiClient.put<Geometry>(`/projects/${projectId}/geometry`, {
        expected_version: input.expectedVersion,
        confirm_base_change: input.confirmBaseChange ?? false,
        buildings: input.buildings,
      }),
    onSuccess: (geometry) => {
      qc.setQueryData(geometryKeys.detail(projectId), geometry);
      void qc.invalidateQueries({ queryKey: ["scene"] });
      void qc.invalidateQueries({ queryKey: ["alternatives", projectId] });
    },
  });
}

/** POST /geometry/validate: server-side BR-14 checks without saving. */
export function useValidateGeometry(projectId: string) {
  return useMutation({
    mutationFn: (buildings: Building[]) =>
      apiClient.post<GeometryValidation>(`/projects/${projectId}/geometry/validate`, { buildings }),
  });
}

export type ImportUnit = "auto" | "m" | "cm" | "mm" | "ft";

export interface ImportInput {
  file: File;
  unit: ImportUnit;
  mode: "append" | "replace";
}

/** POST /geometry/imports (multipart): DXF, STL, OBJ or IFC. */
export function useImportGeometry(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ file, unit, mode }: ImportInput) => {
      const form = new FormData();
      form.append("file", file);
      form.append("unit", unit);
      form.append("mode", mode);
      return apiClient.upload<ImportReport>(`/projects/${projectId}/geometry/imports`, form);
    },
    onSuccess: (report) => {
      if (report.geometry) qc.setQueryData(geometryKeys.detail(projectId), report.geometry);
    },
  });
}
