import { useTranslation } from "react-i18next";
import type { ComparisonDifference } from "@/types/comparisons/comparison.types";
import { describeDifferences } from "./DifferenceList.utils";
import styles from "./DifferenceList.module.css";

/** Why two results cannot be compared, in one sentence with both values. */
export function DifferenceList({ differences }: { differences: ComparisonDifference[] }) {
  const { t } = useTranslation();
  return (
    <section className={styles.root} role="alert">
      <h2 className={styles.title}>{t("compare:incomparable.title")}</h2>
      <p className="reading">{describeDifferences(differences, t)}</p>
    </section>
  );
}
