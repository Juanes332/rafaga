import { useTranslation } from "react-i18next";
import styles from "./FieldErrors.module.css";

interface FieldErrorsProps {
  /** Dotted paths the server rejected (422 details.errors). */
  errors: string[];
  path: string;
}

/** Inline server-side range error for one field. */
export function FieldErrors({ errors, path }: FieldErrorsProps) {
  const { t } = useTranslation();
  if (!errors.includes(path)) return null;
  return <p className={styles.error}>{t("errors:validation_error")}</p>;
}
