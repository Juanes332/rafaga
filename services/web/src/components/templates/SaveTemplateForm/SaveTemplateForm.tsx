import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useSaveTemplateForm } from "./SaveTemplateForm.hook";
import styles from "./SaveTemplateForm.module.css";

/** Save the current configuration as a reusable template. */
export function SaveTemplateForm() {
  const { t } = useTranslation();
  const f = useSaveTemplateForm();
  return (
    <form className={styles.form} onSubmit={f.onSubmit} aria-labelledby="save-template-title">
      <h2 id="save-template-title" className={styles.title}>
        {t("templates:create.title")}
      </h2>
      <div className={styles.field}>
        <Label htmlFor="template-name">{t("templates:create.name")}</Label>
        <Input
          id="template-name"
          value={f.name}
          placeholder={t("templates:create.namePlaceholder")}
          aria-invalid={f.nameError ? true : undefined}
          onChange={(e) => f.setName(e.target.value)}
        />
        {f.nameError ? <p className={styles.error}>{f.nameError}</p> : null}
      </div>
      <div className={styles.field}>
        <Label htmlFor="template-source">{t("templates:create.source")}</Label>
        <Select value={f.projectId} onValueChange={f.setProjectId}>
          <SelectTrigger id="template-source" aria-label={t("templates:create.source")}>
            <SelectValue placeholder={t("users:shares.pickProject")} />
          </SelectTrigger>
          <SelectContent>
            {f.projects.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <p className={styles.hint}>{f.noWind ? t("templates:create.noWind") : t("templates:create.sourceHelp")}</p>
      </div>
      {f.error ? <ErrorNotice error={f.error} /> : null}
      <Button type="submit" disabled={f.pending} className={styles.submit}>
        {t("templates:create.submit")}
      </Button>
    </form>
  );
}
