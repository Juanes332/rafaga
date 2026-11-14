import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { alternativesQueryOptions } from "@/api/alternatives/alternatives.queries";

/** WebGL availability is checked once; without it the plan view remains the way to work. */
export function hasWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return Boolean(canvas.getContext("webgl2") ?? canvas.getContext("webgl"));
  } catch {
    return false;
  }
}

/** Alternative picker for the 3D view; defaults to the base. */
export function useGeometry3D(projectId: string) {
  const alternatives = useQuery(alternativesQueryOptions(projectId));
  const [chosen, setChosen] = useState<string | null>(null);
  const list = alternatives.data ?? [];
  const alternativeId = chosen ?? list.find((a) => a.is_base)?.id ?? list[0]?.id ?? null;
  const [webgl] = useState(hasWebGL);
  return { alternatives: list, alternativeId, setAlternative: setChosen, webgl };
}
