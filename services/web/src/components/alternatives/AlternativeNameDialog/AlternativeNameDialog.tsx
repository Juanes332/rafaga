import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { NO_COPY, useAlternativeNameDialog } from "./AlternativeNameDialog.hook";
import type { AlternativeNameDialogProps } from "./AlternativeNameDialog.types";
import styles from "./AlternativeNameDialog.module.css";

/** Create (optionally copying another alternative) or rename an alternative. */
export function AlternativeNameDialog(props: AlternativeNameDialogProps) {
  const { t } = useTranslation();
  const d = useAlternativeNameDialog(props);
  const create = props.mode === "create";
  return (
    <Dialog open={props.open} onOpenChange={props.onOpenChange}>
      <DialogContent closeLabel={t("common:close")}>
        <form className={styles.form} onSubmit={d.onSubmit}>
          <DialogHeader>
            <DialogTitle>{create ? t("alternatives:createDialog.title") : t("alternatives:renameDialog.title")}</DialogTitle>
            <DialogDescription className="sr-only">{t("alternatives:createDialog.name")}</DialogDescription>
          </DialogHeader>
          <div className={styles.field}>
            <Label htmlFor="alternative-name">{t("alternatives:createDialog.name")}</Label>
            <Input id="alternative-name" autoFocus value={d.name} placeholder={t("alternatives:createDialog.placeholder")} onChange={(e) => d.setName(e.target.value)} />
            {d.nameError ? <ErrorNotice message={d.nameError} /> : null}
          </div>
          {create && props.sources?.length ? (
            <div className={styles.field}>
              <Label htmlFor="alternative-from">{t("alternatives:createDialog.copyFrom")}</Label>
              <Select value={d.from} onValueChange={d.setFrom}>
                <SelectTrigger id="alternative-from">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={NO_COPY}>{t("alternatives:createDialog.copyNone")}</SelectItem>
                  {props.sources.filter((a) => !a.is_base).map((a) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          ) : null}
          {props.error ? <ErrorNotice error={props.error} /> : null}
          <DialogFooter>
            <Button variant="outline" onClick={() => props.onOpenChange(false)}>
              {t("common:cancel")}
            </Button>
            <Button type="submit" disabled={props.pending}>
              {create ? t("alternatives:createDialog.submit") : t("alternatives:renameDialog.submit")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
