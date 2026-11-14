import { Link } from "@tanstack/react-router";
import { ArrowLeftRight, Download, X } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Toggle } from "@/components/ui/toggle";
import type { CompareHeaderProps } from "./CompareHeader.types";
import styles from "./CompareHeader.module.css";

function Picker({ id, label, value, options, onChange }: { id: string; label: string; value?: string; options: CompareHeaderProps["options"]; onChange: (v: string) => void }) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger id={id} aria-label={label} className={styles.picker}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((o) => (
          <SelectItem key={o.resultId} value={o.resultId}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

/** ✕ Salir · A ⇄ B · direction · ΔK · Zonas · Exportar PNG. */
export function CompareHeader(p: CompareHeaderProps) {
  const { t } = useTranslation();
  return (
    <header className={styles.root}>
      <Button variant="ghost" size="sm" asChild>
        <Link to="/projects/$projectId/simulate" params={{ projectId: p.projectId }}>
          <X aria-hidden />
          {t("compare:exit")}
        </Link>
      </Button>
      <h1 className="sr-only">{t("compare:title")}</h1>
      <div className={styles.pair}>
        <span className={styles.side}>{t("compare:a")}</span>
        <Picker id="compare-a" label={t("compare:pickA")} value={p.a} options={p.options} onChange={(v) => p.onPick("a", v)} />
        <Button variant="ghost" size="icon" aria-label={t("compare:swap")} onClick={p.onSwap}>
          <ArrowLeftRight aria-hidden />
        </Button>
        <span className={styles.side}>{t("compare:b")}</span>
        <Picker id="compare-b" label={t("compare:pickB")} value={p.b} options={p.options} onChange={(v) => p.onPick("b", v)} />
      </div>
      {p.direction ? <span className={styles.direction}>{t("compare:direction", { direction: p.direction })}</span> : null}
      <div className={styles.tools}>
        <Toggle pressed={p.deltaK} onPressedChange={p.onToggleDeltaK} title={t("compare:deltaKHelp")}>
          {t("compare:deltaK")}
        </Toggle>
        <Toggle pressed={p.zones} onPressedChange={p.onToggleZones}>
          {t("compare:zones")}
        </Toggle>
        {p.canExport ? (
          <Button variant="outline" size="sm" onClick={p.onExport}>
            <Download aria-hidden />
            {t("results:export")}
          </Button>
        ) : null}
      </div>
    </header>
  );
}
