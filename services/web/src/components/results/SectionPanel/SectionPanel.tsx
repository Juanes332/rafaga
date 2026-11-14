import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Button } from "@/components/ui/button";
import { formatUnit } from "@/lib/format/format.number";
import { useSectionPanel } from "./SectionPanel.hook";
import type { SectionPanelProps } from "./SectionPanel.types";
import styles from "./SectionPanel.module.css";

/** Inspector while tracing a vertical section. */
export function SectionPanel(props: SectionPanelProps) {
  const { t } = useTranslation();
  const s = useSectionPanel(props);
  return (
    <section className={styles.root} aria-labelledby="section-title">
      <h2 id="section-title" className={styles.title}>
        {t("results:section.title")}
      </h2>
      <p className="reading">{t("results:section.lead")}</p>
      {!s.complete ? <p className={styles.hint}>{t("results:section.needTwo")}</p> : null}
      {s.length !== null ? (
        <p>
          {t("results:section.length")}: <span className="num">{formatUnit(s.length, 0, "m")}</span>
        </p>
      ) : null}
      {s.against ? <ErrorNotice message={t("results:section.against")} /> : null}
      {s.error ? <ErrorNotice error={s.error} /> : null}
      <div className={styles.actions}>
        <Button disabled={!s.canLaunch} onClick={s.launch}>
          {s.pending ? t("results:section.launching") : t("results:section.launch")}
        </Button>
        {s.section.length > 0 ? (
          <Button variant="outline" onClick={s.clear}>
            {t("results:section.clear")}
          </Button>
        ) : null}
      </div>
    </section>
  );
}
