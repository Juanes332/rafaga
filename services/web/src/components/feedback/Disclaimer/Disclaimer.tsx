import { useTranslation } from "react-i18next";
import { cn } from "@/lib/utils";
import styles from "./Disclaimer.module.css";

/** FR-48 strip: permanent on every result, comparison and export view. Information, not an error. */
export function Disclaimer({ className }: { className?: string }) {
  const { t } = useTranslation();
  return (
    <div className={cn(styles.root, className)} data-testid="disclaimer">
      <p>{t("common:disclaimer")}</p>
      <details className={styles.more}>
        <summary>{t("common:disclaimerMore")}</summary>
        <p>{t("common:disclaimerNote")}</p>
      </details>
    </div>
  );
}
