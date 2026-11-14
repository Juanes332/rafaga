import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useWindPanel } from "./WindPanel.hook";
import type { WindPanelProps } from "./WindPanel.types";
import styles from "./WindPanel.module.css";

/** Inspector for SCR-10: source, manual wind, terrain and air density. */
export function WindPanel(p: WindPanelProps) {
  const { t } = useTranslation();
  const v = useWindPanel(p);
  const w = p.wind;
  return (
    <>
      {w ? (
      <section className={styles.group}>
        <h2 className={styles.title}>{t("wind:source.label")}</h2>
        <p className={styles.muted}>{p.manual ? t("wind:source.manual") : t("wind:source.era5")}</p>
        {v.sourceNote ? <p className={styles.muted}>{v.sourceNote}</p> : null}
        {!p.readOnly ? (
          <div className={styles.actions}>
            <Button variant={w?.rose ? "outline" : "default"} disabled={p.fetching} onClick={p.onFetch}>
              {p.fetching ? t("wind:fetching") : w?.rose ? t("wind:refetch") : t("wind:fetch")}
            </Button>
            {!p.manual ? (
              <Button variant="ghost" onClick={p.onManual}>
                {t("wind:offline.manual")}
              </Button>
            ) : null}
          </div>
        ) : null}
      </section>
      ) : null}
      {p.manual && w ? (
        <section className={styles.group}>
          <h2 className={styles.title}>{t("wind:manual.title")}</h2>
          <ParamField id="manual-dir" label={t("wind:manual.direction")} unit="°" min={0} max={360} decimals={0} value={w.manual_direction_deg ?? null} help={t("wind:manual.directionHelp")} disabled={p.readOnly} onCommit={(v2) => p.onPatch({ source: "manual", manual_direction_deg: v2 })} />
          <ParamField id="manual-u10" label={t("wind:manual.speed")} unit="m/s" min={0.5} max={60} decimals={1} value={w.manual_u10_ms ?? null} help={t("wind:manual.speedHelp")} disabled={p.readOnly} onCommit={(v2) => p.onPatch({ source: "manual", manual_u10_ms: v2 })} />
        </section>
      ) : null}
      {w ? (
        <section className={styles.group}>
          <Label htmlFor="terrain">{t("wind:terrain.label")}</Label>
          <Select value={v.terrainValue} onValueChange={v.onTerrain} disabled={p.readOnly}>
            <SelectTrigger id="terrain">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {p.terrain.map((c) => (
                <SelectItem key={c.key} value={c.key}>
                  {t(`wind:terrain.${c.key}`)}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <ParamField id="z0" label={t("wind:terrain.z0")} unit="m" min={0.0001} max={3} decimals={4} value={w.z0_m} help={t("glossary:roughness")} disabled={p.readOnly} onCommit={(z0) => p.onPatch({ z0_m: z0 })} />
        </section>
      ) : null}
      {p.patchError ? <ErrorNotice error={p.patchError} /> : null}
      <section className={styles.group}>
        <h2 className={styles.title}>{t("wind:density.title")}</h2>
        <p className={styles.value}>{v.densityText}</p>
        <p className={styles.formula}>{t("wind:density.formula")}</p>
        {v.densityDetail ? <p className={styles.muted}>{v.densityDetail}</p> : null}
      </section>
    </>
  );
}
