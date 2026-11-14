import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useProjectNameDialog } from "./ProjectNameDialog.hook";
import type { ProjectNameDialogProps } from "./ProjectNameDialog.types";
import styles from "./ProjectNameDialog.module.css";

/** Create or rename a project: one name field. */
export function ProjectNameDialog(props: ProjectNameDialogProps) {
  const { t } = useTranslation();
  const d = useProjectNameDialog(props);
  return (
    <Dialog open={props.open} onOpenChange={props.onOpenChange}>
      <DialogContent closeLabel={t("common:close")}>
        <form onSubmit={d.onSubmit} className={styles.form}>
          <DialogHeader>
            <DialogTitle>{props.title}</DialogTitle>
            <DialogDescription className="sr-only">{t("projects:create.name")}</DialogDescription>
          </DialogHeader>
          <div className={styles.field}>
            <Label htmlFor="project-name">{t("projects:create.name")}</Label>
            <Input
              id="project-name"
              value={d.name}
              autoFocus
              placeholder={t("projects:create.namePlaceholder")}
              aria-invalid={d.nameError ? true : undefined}
              onChange={(e) => d.setName(e.target.value)}
            />
            {d.nameError ? <ErrorNotice message={d.nameError} /> : null}
          </div>
          {props.error ? <ErrorNotice error={props.error} /> : null}
          <DialogFooter>
            <Button variant="outline" onClick={() => props.onOpenChange(false)}>
              {t("common:cancel")}
            </Button>
            <Button type="submit" disabled={props.pending}>
              {props.submitLabel}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
