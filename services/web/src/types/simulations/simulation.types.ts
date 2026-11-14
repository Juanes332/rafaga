import type { components } from "@/types/api/openapi.gen";

type S = components["schemas"];

export type SectionLine = S["SectionLine"];
export type OutputGrid = S["OutputGrid"];
export type OutputGridPlan = S["OutputGridPlan"];
export type OutputGridSection = S["OutputGridSection"];
export type EstimateRequest = S["EstimateRequest"];
export type Estimate = S["Estimate"];
export type SimulationCreate = S["SimulationCreate"];
export type JobError = S["JobError"];
export type Job = S["Job"];
export type Study = S["Study"];
export type StudySummary = S["StudySummary"];
