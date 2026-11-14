import type { components } from "@/types/api/openapi.gen";

type S = components["schemas"];

export type Thresholds = S["Thresholds"];
export type Settings = S["Settings"];
export type SettingsPatch = S["SettingsPatch"];
export type TemplatePayload = S["TemplatePayload"];
export type Template = S["Template"];
export type TemplateCreate = S["TemplateCreate"];
export type ApplyTemplate = S["ApplyTemplate"];
