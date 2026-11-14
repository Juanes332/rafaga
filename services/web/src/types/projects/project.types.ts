import type { components } from "@/types/api/openapi.gen";

type S = components["schemas"];

export type Project = S["Project"];
export type ProjectSummary = S["ProjectSummary"];
export type ProjectCreate = S["ProjectCreate"];
export type ProjectPatch = S["ProjectPatch"];
export type LocationRequest = S["LocationRequest"];
