import { useTranslation } from "react-i18next";
import { nextTheme, useThemeStore, type ThemeChoice } from "@/stores/theme/theme.store";

interface UseThemeToggle {
  theme: ThemeChoice;
  label: string;
  onToggle: () => void;
}

/** Cycles light → dark → system and names the current state for screen readers. */
export function useThemeToggle(): UseThemeToggle {
  const { t } = useTranslation();
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);
  return {
    theme,
    label: `${t("common:theme.toggle")}: ${t(`common:theme.${theme}`)}`,
    onToggle: () => setTheme(nextTheme(theme)),
  };
}
