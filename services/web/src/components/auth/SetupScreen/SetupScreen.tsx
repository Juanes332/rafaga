import { useTranslation } from "react-i18next";
import { AuthLayout } from "@/components/auth/AuthLayout/AuthLayout";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useSetupScreen } from "./SetupScreen.hook";
import styles from "./SetupScreen.module.css";

/** SCR-01: create the local architect account on first run. */
export function SetupScreen() {
  const { t } = useTranslation();
  const s = useSetupScreen();
  return (
    <AuthLayout>
      <h1 className={styles.title}>{t("auth:setup.title")}</h1>
      <p className={styles.lead}>{t("auth:setup.lead")}</p>
      <form className={styles.form} onSubmit={s.onSubmit} noValidate>
        <div className={styles.field}>
          <Label htmlFor="setup-email">{t("auth:email")}</Label>
          <Input id="setup-email" type="email" autoComplete="email" required value={s.email} onChange={(e) => s.setEmail(e.target.value)} />
        </div>
        <div className={styles.field}>
          <Label htmlFor="setup-password">{t("auth:password")}</Label>
          <Input
            id="setup-password"
            type="password"
            autoComplete="new-password"
            required
            minLength={10}
            value={s.password}
            aria-invalid={s.passwordError ? true : undefined}
            aria-describedby="setup-password-hint"
            onChange={(e) => s.setPassword(e.target.value)}
          />
          <p id="setup-password-hint" className={s.passwordError ? styles.error : styles.hint}>
            {s.passwordError ?? t("auth:passwordHint")}
          </p>
        </div>
        {s.formError ? <ErrorNotice error={s.formError} /> : null}
        <Button type="submit" disabled={s.pending} className={styles.submit}>
          {s.pending ? t("auth:setup.submitting") : t("auth:setup.submit")}
        </Button>
      </form>
    </AuthLayout>
  );
}
