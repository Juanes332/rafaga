import type { TFunction } from "i18next";
import { directionLabel } from "@/lib/format/format.direction";
import { formatUnit } from "@/lib/format/format.number";
import type { ComparisonDifference } from "@/types/comparisons/comparison.types";

const num = (v: unknown): number | null => (typeof v === "number" && Number.isFinite(v) ? v : null);

function formatValue(field: ComparisonDifference["field"], v: unknown, t: TFunction): string {
  const n = num(v);
  switch (field) {
    case "kind":
      return t(`compare:kinds.${String(v)}`, { defaultValue: String(v) });
    case "direction":
      return n === null ? "—" : directionLabel(n);
    case "dx":
    case "analysis_height":
      return formatUnit(n, 1, "m");
    case "z0":
      return formatUnit(n, 2, "m");
    case "u_ref":
      return formatUnit(n, 1, "m/s");
    default:
      return String(v ?? "—");
  }
}

function joinList(parts: string[], and: string): string {
  if (parts.length <= 1) return parts.join("");
  return `${parts.slice(0, -1).join(", ")} ${and} ${parts[parts.length - 1]}`;
}

/** One plain sentence naming every parameter that differs, with both values. */
export function describeDifferences(diffs: ComparisonDifference[], t: TFunction): string {
  const parts = diffs.map((d) =>
    t(`compare:incomparable.${d.field}`, { a: formatValue(d.field, d.a, t), b: formatValue(d.field, d.b, t) }),
  );
  return t("compare:incomparable.sentence", { list: joinList(parts, t("compare:incomparable.and")) });
}
