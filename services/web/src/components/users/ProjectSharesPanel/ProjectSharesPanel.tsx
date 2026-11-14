import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { useProjectSharesPanel } from "./ProjectSharesPanel.hook";
import styles from "./ProjectSharesPanel.module.css";

/** Share or revoke one project per user. */
export function ProjectSharesPanel({ selfId }: { selfId: string | undefined }) {
  const { t } = useTranslation();
  const p = useProjectSharesPanel(selfId);
  return (
    <section className={styles.root} aria-labelledby="shares-title">
      <h2 id="shares-title" className={styles.title}>
        {t("users:shares.title")}
      </h2>
      {p.projects.length === 0 ? <p className={styles.note}>{t("users:shares.noProjects")}</p> : null}
      <div className={styles.field}>
        <Label htmlFor="shares-project">{t("users:shares.project")}</Label>
        <Select value={p.projectId} onValueChange={p.setProjectId}>
          <SelectTrigger id="shares-project" aria-label={t("users:shares.project")} className={styles.select}>
            <SelectValue placeholder={t("users:shares.pickProject")} />
          </SelectTrigger>
          <SelectContent>
            {p.projects.map((proj) => (
              <SelectItem key={proj.id} value={proj.id}>
                {proj.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      {p.error ? <ErrorNotice error={p.error} /> : null}
      {p.projectId && p.others.length === 0 ? <p className={styles.note}>{t("users:shares.noOthers")}</p> : null}
      {p.projectId && !p.loadingShares ? (
        <ul className={styles.list}>
          {p.others.map((u) => (
            <li key={u.id} className={styles.row}>
              <Switch
                id={`share-${u.id}`}
                checked={p.isShared(u.id)}
                disabled={p.pending}
                aria-label={t("users:shares.grant", { email: u.email })}
                onCheckedChange={(c) => p.onToggle(u, c)}
              />
              <label htmlFor={`share-${u.id}`} className={styles.email}>
                {u.email}
              </label>
              <span className={styles.state}>
                {t(`users:roles.${u.role}`)}, {p.isShared(u.id) ? t("users:shares.hasAccess") : t("users:shares.noAccess")}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
