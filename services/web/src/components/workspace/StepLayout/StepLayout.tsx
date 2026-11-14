import { SlidersHorizontal } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet";
import { useStepLayout } from "./StepLayout.hook";
import type { StepLayoutProps } from "./StepLayout.types";
import styles from "./StepLayout.module.css";

/** Central canvas + right inspector; the inspector folds into a sheet on narrow screens. */
export function StepLayout({ title, canvas, inspector, toolbar, footer }: StepLayoutProps) {
  const { t } = useTranslation();
  const l = useStepLayout();
  return (
    <div className={styles.root}>
      <h1 className="sr-only">{title}</h1>
      <div className={inspector && l.docked ? styles.grid : styles.single}>
        <section className={styles.canvasCol} aria-label={title}>
          {toolbar ? <div className={styles.toolbar}>{toolbar}</div> : null}
          {inspector && !l.docked ? (
            <div className={styles.sheetBar}>
              <Button variant="secondary" size="sm" onClick={() => l.setOpen(true)}>
                <SlidersHorizontal aria-hidden />
                {t("workspace:inspector.open")}
              </Button>
            </div>
          ) : null}
          <div className={styles.canvas}>{canvas}</div>
        </section>
        {inspector && l.docked ? (
          <aside className={styles.inspector} aria-label={t("workspace:inspector.title")}>
            {inspector}
          </aside>
        ) : null}
      </div>
      {inspector && !l.docked ? (
        <Sheet open={l.open} onOpenChange={l.setOpen}>
          <SheetContent side={l.sheetSide} closeLabel={t("workspace:inspector.close")}>
            <SheetTitle>{title}</SheetTitle>
            <SheetDescription className="sr-only">{t("workspace:inspector.title")}</SheetDescription>
            {inspector}
          </SheetContent>
        </Sheet>
      ) : null}
      {footer}
    </div>
  );
}
