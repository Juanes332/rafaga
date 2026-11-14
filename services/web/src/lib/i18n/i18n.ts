import i18next, { type Resource } from "i18next";
import { initReactI18next } from "react-i18next";

// Every namespace is a JSON file in locales/es-CO; adding a file adds a namespace.
const files = import.meta.glob<{ default: Record<string, unknown> }>("../../locales/es-CO/*.json", { eager: true });

function buildResources(): Resource {
  const ns: Record<string, Record<string, unknown>> = {};
  for (const [path, mod] of Object.entries(files)) {
    const name = path.split("/").pop()?.replace(".json", "") ?? "common";
    ns[name] = mod.default;
  }
  return { "es-CO": ns };
}

/** Initialise i18next synchronously so the first render already has copy. */
export function initI18n(): typeof i18next {
  if (!i18next.isInitialized) {
    void i18next.use(initReactI18next).init({
      lng: "es-CO",
      fallbackLng: "es-CO",
      defaultNS: "common",
      resources: buildResources(),
      initAsync: false,
      interpolation: { escapeValue: false },
      returnNull: false,
    });
  }
  return i18next;
}

export const i18n = i18next;
