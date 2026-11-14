import { useTranslation } from "react-i18next";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import styles from "./ManualElevation.module.css";

interface ManualElevationProps {
  pending: boolean;
  onSubmit: (elevation: number) => void;
}

/** Shown after 503 elevation_unavailable: the user types the altitude. */
export function ManualElevation({ pending, onSubmit }: ManualElevationProps) {
  const { t } = useTranslation();
  return (
    <section className={styles.root} role="alert" aria-busy={pending}>
      <h2 className={styles.title}>{t("location:elevation.title")}</h2>
      <p className={styles.lead}>{t("location:elevation.lead")}</p>
      <ParamField id="manual-elevation" label={t("location:elevation.label")} unit="m" min={-500} max={9000} decimals={0} value={null} onCommit={onSubmit} />
    </section>
  );
}
