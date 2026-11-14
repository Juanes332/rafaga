import { setupServer } from "msw/node";
import { handlers } from "./handlers";

/** Shared MSW server for Vitest. */
export const server = setupServer(...handlers);
