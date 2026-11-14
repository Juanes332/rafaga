import { create } from "zustand";
import { persist } from "zustand/middleware";

export type ThemeChoice = "light" | "dark" | "system";

interface ThemeState {
  theme: ThemeChoice;
  setTheme: (theme: ThemeChoice) => void;
}

export function nextTheme(theme: ThemeChoice): ThemeChoice {
  return theme === "light" ? "dark" : theme === "dark" ? "system" : "light";
}

/** Without a choice the CSS follows prefers-color-scheme, so the attribute is removed. */
export function applyTheme(theme: ThemeChoice): void {
  const root = document.documentElement;
  if (theme === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", theme);
}

/** Theme choice (FR-52), persisted per browser. */
export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      theme: "system",
      setTheme: (theme) => {
        applyTheme(theme);
        set({ theme });
      },
    }),
    { name: "rafaga-theme", onRehydrateStorage: () => (state) => state && applyTheme(state.theme) },
  ),
);

/** Resolved light/dark, for canvases that cannot read CSS media queries. */
export function resolvedTheme(theme: ThemeChoice): "light" | "dark" {
  if (theme !== "system") return theme;
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}
