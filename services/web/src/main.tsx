import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { Providers } from "./app/providers";
import { ServiceMissing } from "./components/feedback/ServiceMissing/ServiceMissing";
import { loadRuntimeConfig } from "./lib/config/runtime-config";
import { configureApiClient } from "./lib/http/api-client";
import { initI18n } from "./lib/i18n/i18n";
import { useSessionStore } from "./stores/session/session.store";
import { applyTheme, useThemeStore } from "./stores/theme/theme.store";
import "./styles/globals.css";

async function bootstrap(): Promise<void> {
  initI18n();
  applyTheme(useThemeStore.getState().theme);
  // Mock mode serves the whole API from MSW fixtures; the import is dropped from production builds.
  if (import.meta.env.MODE === "mock") {
    const { startMockWorker } = await import("../tests/msw/browser");
    await startMockWorker();
  }
  const root = createRoot(document.getElementById("root") as HTMLElement);
  const apiBase = await loadRuntimeConfig(fetch.bind(window), window.location);
  if (!apiBase) {
    root.render(<ServiceMissing />);
    return;
  }
  configureApiClient({
    baseUrl: apiBase,
    getToken: () => useSessionStore.getState().token,
    onUnauthorized: () => useSessionStore.getState().expire(),
  });
  root.render(
    <StrictMode>
      <Providers />
    </StrictMode>,
  );
}

void bootstrap();
