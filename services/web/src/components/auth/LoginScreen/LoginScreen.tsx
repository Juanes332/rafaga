import { useTranslation } from "react-i18next";
import { AuthLayout } from "@/components/auth/AuthLayout/AuthLayout";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLoginScreen } from "./LoginScreen.hook";
import styles from "@/components/auth/SetupScreen/SetupScreen.module.css";

/** SCR-02: sign in with the local account. */
export function LoginScreen() {
  const { t } = useTranslation();
  const s = useLoginScreen();
  return (
    <AuthLayout>
      <h1 className={styles.title}>{t("auth:login.title")}</h1>
      <p className={styles.lead}>{s.expired ? t("auth:sessionExpired") : t("auth:login.lead")}</p>
      <form className={styles.form} onSubmit={s.onSubmit}>
        <div className={styles.field}>
          <Label htmlFor="login-email">{t("auth:email")}</Label>
          <Input id="login-email" type="email" autoComplete="email" required value={s.email} onChange={(e) => s.setEmail(e.target.value)} />
        </div>
        <div className={styles.field}>
          <Label htmlFor="login-password">{t("auth:password")}</Label>
          <Input
            id="login-password"
            type="password"
            autoComplete="current-password"
            required
            value={s.password}
            onChange={(e) => s.setPassword(e.target.value)}
          />
        </div>
        {s.message ? <ErrorNotice message={s.message} /> : null}
        <Button type="submit" disabled={s.pending} className={styles.submit}>
          {s.pending ? t("auth:login.submitting") : t("auth:login.submit")}
        </Button>
      </form>
    </AuthLayout>
  );
}
