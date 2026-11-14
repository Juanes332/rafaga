import type { TFunction } from "i18next";
import { THIN } from "@/lib/format/format.number";
import { errorMessage } from "@/lib/http/error-copy";
import { hasCode, isApiError } from "@/lib/http/api-error";

export const IMPORT_MAX_BYTES = 100 * 1024 * 1024;
export const IMPORT_ACCEPT = ".dxf,.stl,.obj,.ifc";

/** Import-specific copy: base_locked has no confirm flag here, import_failed carries a hint key. */
export function importErrorText(error: unknown, t: TFunction): string | null {
  if (!error) return null;
  if (hasCode(error, "base_locked")) return t("errors:base_locked_import");
  if (hasCode(error, "import_failed") && isApiError(error)) {
    const key = typeof error.details.hint_key === "string" ? `geometry:import.hints.${error.details.hint_key}` : null;
    const hint = key && t(key) !== key ? t(key) : t("errors:import_failed_default");
    return t("errors:import_failed", { hint });
  }
  return errorMessage(error);
}

export function formatMegabytes(bytes: number): string {
  return `${(bytes / 1024 / 1024).toFixed(1).replace(".", ",")}${THIN}MB`;
}
