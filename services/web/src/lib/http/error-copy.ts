import { i18n } from "@/lib/i18n/i18n";
import { formatNumber } from "@/lib/format/format.number";
import { isApiError } from "./api-error";

function num(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function specialCase(code: string, details: Record<string, unknown>, retryAfter: number | null): string | null {
  if (code === "rate_limited") {
    return retryAfter ? i18n.t("errors:rate_limited", { seconds: retryAfter }) : i18n.t("errors:rate_limited_nowait");
  }
  if (code === "mesh_too_large") {
    const dx = num(details.proposed_dx_m);
    return dx ? i18n.t("errors:mesh_too_large", { dx: formatNumber(dx, 2).replace(/,?0+$/, "") }) : null;
  }
  if (code === "alternatives_limit") return i18n.t("errors:alternatives_limit", { limit: num(details.limit) ?? 8 });
  if (code === "upload_too_large") {
    const mb = num(details.limit_mb) ?? (num(details.limit_bytes) ? Math.round((num(details.limit_bytes) ?? 0) / 1e6) : null);
    return i18n.t("errors:upload_too_large", { limit: mb ? `${mb} MB` : "permitido" });
  }
  return null;
}

/** es-CO copy (cause + fix) for any failure; the server's English message never reaches the UI. */
export function errorMessage(error: unknown): string {
  if (!isApiError(error)) return i18n.t("errors:generic");
  const special = specialCase(error.code, error.details, error.retryAfter);
  if (special) return special;
  const key = `errors:${error.code}`;
  return i18n.exists(key) ? i18n.t(key) : i18n.t("errors:generic");
}

/** Same mapping for job errors, which carry only a code. */
export function jobErrorMessage(code: string | null | undefined): string {
  if (!code) return i18n.t("errors:internal_error");
  const key = `errors:${code}`;
  return i18n.exists(key) ? i18n.t(key) : i18n.t("errors:internal_error");
}
