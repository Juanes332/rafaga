import { Box, Map as MapIcon, Ruler } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Toggle } from "@/components/ui/toggle";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useResultsToolbar } from "./ResultsToolbar.hook";
import type { ResultsToolbarProps } from "./ResultsToolbar.types";
import styles from "./ResultsToolbar.module.css";

/** Direction · layer · zones · section · 3D, above the canvas. */
export function ResultsToolbar(p: ResultsToolbarProps) {
  const { t } = useTranslation();
  const b = useResultsToolbar();
  const plan = p.kind !== "section2d" && !b.view3d;
  return (
    <>
      {p.directions.length > 0 ? (
        <div className={styles.group}>
          <Label htmlFor="result-direction">{t("results:direction")}</Label>
          <Select value={p.resultId} onValueChange={p.onDirection}>
            <SelectTrigger id="result-direction" className={styles.select} title={t("results:directionHelp")}>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {p.directions.map((d) => (
                <SelectItem key={d.resultId} value={d.resultId}>
                  {d.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      ) : null}
      {plan ? (
        <ToggleGroup type="single" value={b.layer} onValueChange={b.onLayer} aria-label={t("results:layer.label")}>
          {(["k", "speed", "lawson"] as const).map((l) => (
            <ToggleGroupItem key={l} value={l}>
              {t(`results:layer.${l}`)}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      ) : null}
      {plan ? (
        <Toggle pressed={b.zones} onPressedChange={b.toggleZones} title={t("results:zonesHelp")}>
          {t("results:zones")}
        </Toggle>
      ) : null}
      <span className={styles.spacer} />
      {plan && !p.readOnly ? (
        <Toggle pressed={b.tool === "section"} onPressedChange={b.toggleSection}>
          <Ruler aria-hidden />
          {t("results:section.tool")}
        </Toggle>
      ) : null}
      {p.kind === "volume3d" ? (
        <Button variant="outline" size="sm" onClick={b.toggle3d}>
          {b.view3d ? <MapIcon aria-hidden /> : <Box aria-hidden />}
          {b.view3d ? t("results:view3d.close") : t("results:view3d.open")}
        </Button>
      ) : null}
      {b.tool === "section" ? <p className={styles.hint}>{t("results:section.toolActive")}</p> : null}
    </>
  );
}
