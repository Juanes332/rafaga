import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { useCreateUserForm } from "./CreateUserForm.hook";
import styles from "./CreateUserForm.module.css";

/** Create an architect or reviewer account. */
export function CreateUserForm() {
  const { t } = useTranslation();
  const f = useCreateUserForm();
  return (
    <form className={styles.form} onSubmit={f.onSubmit} aria-labelledby="create-user-title">
      <h2 id="create-user-title" className={styles.title}>
        {t("users:create.title")}
      </h2>
      <div className={styles.field}>
        <Label htmlFor="new-user-email">{t("users:create.email")}</Label>
        <Input id="new-user-email" type="email" autoComplete="off" required value={f.email} onChange={(e) => f.setEmail(e.target.value)} />
      </div>
      <div className={styles.field}>
        <Label htmlFor="new-user-password">{t("users:create.password")}</Label>
        <Input
          id="new-user-password"
          type="password"
          autoComplete="new-password"
          value={f.password}
          aria-invalid={f.passwordError ? true : undefined}
          aria-describedby="new-user-password-hint"
          onChange={(e) => f.setPassword(e.target.value)}
        />
        <p id="new-user-password-hint" className={f.passwordError ? styles.error : styles.hint}>
          {f.passwordError ?? t("users:create.passwordHint")}
        </p>
      </div>
      <fieldset className={styles.roles}>
        <legend className={styles.legend}>{t("users:create.role")}</legend>
        <RadioGroup value={f.role} onValueChange={f.setRole} className={styles.roleRow}>
          {(["reviewer", "architect"] as const).map((r) => (
            <div key={r} className={styles.option}>
              <RadioGroupItem id={`new-user-role-${r}`} value={r} />
              <Label htmlFor={`new-user-role-${r}`}>{t(`users:roles.${r}`)}</Label>
            </div>
          ))}
        </RadioGroup>
      </fieldset>
      {f.error ? <ErrorNotice error={f.error} /> : null}
      <Button type="submit" disabled={f.pending} className={styles.submit}>
        {t("users:create.submit")}
      </Button>
    </form>
  );
}
