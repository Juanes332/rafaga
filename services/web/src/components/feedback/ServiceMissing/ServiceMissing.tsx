import { useTranslation } from "react-i18next";
import { AuthLayout } from "@/components/auth/AuthLayout/AuthLayout";
import { Button } from "@/components/ui/button";
import styles from "./ServiceMissing.module.css";

/** WEB-01 failure: /config.json missing or invalid. */
export function ServiceMissing() {
  const { t } = useTranslation();
  return (
    <AuthLayout>
      <h1 className={styles.title} role="alert">
        {t("common:serviceMissing")}
      </h1>
      <p className={styles.help}>{t("common:serviceMissingHelp")}</p>
      <Button className={styles.action} onClick={() => window.location.reload()}>
        {t("common:reload")}
      </Button>
    </AuthLayout>
  );
}
