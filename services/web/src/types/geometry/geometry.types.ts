import type { components } from "@/types/api/openapi.gen";

type S = components["schemas"];

export type Tier = S["Tier"];
export type Building = S["Building"];
export type GeometryIssue = S["GeometryIssue"];
export type Geometry = S["Geometry"];
export type GeometryPut = S["GeometryPut"];
export type GeometryValidateRequest = S["GeometryValidateRequest"];
export type GeometryValidation = S["GeometryValidation"];
export type ImportReport = S["ImportReport"];
export type BackgroundPlan = S["BackgroundPlan"];
export type BackgroundPatch = S["BackgroundPatch"];
