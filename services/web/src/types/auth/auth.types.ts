import type { components } from "@/types/api/openapi.gen";

type S = components["schemas"];

export type User = S["User"];
export type Credentials = S["Credentials"];
export type LoginRequest = S["LoginRequest"];
export type Token = S["Token"];
export type SetupStatus = S["SetupStatus"];
