import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { Template } from "@/types/settings/settings.types";
import { useApplyTemplateDialog } from "./ApplyTemplateDialog.hook";
import styles from "./ApplyTemplateDialog.module.css";

interface ApplyTemplateDialogProps {
  template: Template | null;
  onClose: () => void;
}

/** Apply a template's terrain and defaults to one project. */
export function ApplyTemplateDialog({ template, onClose }: ApplyTemplateDialogProps) {
  const { t } = useTranslation();
  const d = useApplyTemplateDialog(template, onClose);
  return (
    <Dialog open={template !== null} onOpenChange={(o) => !o && onClose()}>
      <DialogContent closeLabel={t("common:close")}>
        <DialogHeader>
          <DialogTitle>{t("templates:apply.title", { name: template?.name })}</DialogTitle>
          <DialogDescription>{t("templates:apply.body")}</DialogDescription>
        </DialogHeader>
        <div className={styles.field}>
          <Label htmlFor="apply-project">{t("templates:apply.project")}</Label>
          <Select value={d.projectId} onValueChange={d.setProjectId}>
            <SelectTrigger id="apply-project" aria-label={t("templates:apply.project")}>
              <SelectValue placeholder={t("users:shares.pickProject")} />
            </SelectTrigger>
            <SelectContent>
              {d.projects.map((p) => (
                <SelectItem key={p.id} value={p.id}>
                  {p.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {d.error ? <ErrorNotice error={d.error} /> : null}
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            {t("common:cancel")}
          </Button>
          <Button onClick={d.onApply} disabled={!d.projectId || d.pending}>
            {t("templates:apply.submit")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
