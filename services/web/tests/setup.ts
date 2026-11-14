import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll, beforeEach } from "vitest";
import { configureApiClient } from "@/lib/http/api-client";
import { initI18n } from "@/lib/i18n/i18n";
import { useSessionStore } from "@/stores/session/session.store";
import { server } from "./msw/server";
import { API } from "./msw/api-base";
import { resetMockState } from "./msw/mock-state";
import { installBrowserStubs } from "./utils/browser-stubs";

declare global {
  var IS_REACT_ACT_ENVIRONMENT: boolean;
}

globalThis.IS_REACT_ACT_ENVIRONMENT = true;
installBrowserStubs();
initI18n();

// Unhandled requests fail loudly: an un-mocked call is a test bug, not a warning.
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

beforeEach(() => {
  configureApiClient({
    baseUrl: API,
    getToken: () => useSessionStore.getState().token,
    onUnauthorized: () => useSessionStore.getState().expire(),
  });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
  resetMockState();
  sessionStorage.clear();
  localStorage.clear();
});

afterAll(() => server.close());
