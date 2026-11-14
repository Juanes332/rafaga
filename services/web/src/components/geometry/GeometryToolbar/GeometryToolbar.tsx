import { Box, Image as ImageIcon, Map as MapIcon, MousePointer2, Pentagon, Redo2, Ruler, Square, Undo2, Upload } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { TOOLS, useGeometryToolbar } from "./GeometryToolbar.hook";
import type { GeometryToolbarProps } from "./GeometryToolbar.types";
import styles from "./GeometryToolbar.module.css";

const ICONS = { select: MousePointer2, rect: Square, polygon: Pentagon, ruler: Ruler } as const;

/** Tools, undo/redo, plan/3D, import/trace and save. */
export function GeometryToolbar(p: GeometryToolbarProps) {
  const { t } = useTranslation();
  const tb = useGeometryToolbar();
  return (
    <div className={styles.root}>
      {!p.readOnly && tb.view === "plan" ? (
        <ToggleGroup type="single" value={tb.tool} onValueChange={tb.onTool} aria-label={t("geometry:tools.label")}>
          {TOOLS.map((tool) => {
            const Icon = ICONS[tool];
            return (
              <ToggleGroupItem key={tool} value={tool} aria-label={t(`geometry:tools.${tool}`)} title={t(`geometry:tools.${tool}`)}>
                <Icon aria-hidden />
              </ToggleGroupItem>
            );
          })}
        </ToggleGroup>
      ) : null}
      {!p.readOnly ? (
        <div className={styles.group}>
          <Button variant="ghost" size="icon" aria-label={t("geometry:tools.undo")} title={t("geometry:tools.undo")} disabled={!tb.canUndo} onClick={tb.undo}>
            <Undo2 aria-hidden />
          </Button>
          <Button variant="ghost" size="icon" aria-label={t("geometry:tools.redo")} title={t("geometry:tools.redo")} disabled={!tb.canRedo} onClick={tb.redo}>
            <Redo2 aria-hidden />
          </Button>
        </div>
      ) : null}
      <ToggleGroup type="single" value={tb.view} onValueChange={tb.onView} aria-label={t("geometry:tools.viewLabel")}>
        <ToggleGroupItem value="plan">
          <MapIcon aria-hidden />
          {t("geometry:tools.plan")}
        </ToggleGroupItem>
        <ToggleGroupItem value="3d">
          <Box aria-hidden />
          {t("geometry:tools.view3d")}
        </ToggleGroupItem>
      </ToggleGroup>
      <div className={styles.spacer} />
      {!p.readOnly ? (
        <div className={styles.group}>
          <Button variant="ghost" size="sm" onClick={p.onImport}>
            <Upload aria-hidden />
            {t("geometry:importFile")}
          </Button>
          <Button variant="ghost" size="sm" onClick={p.onTrace}>
            <ImageIcon aria-hidden />
            {t("geometry:trace")}
          </Button>
          <Button variant="outline" size="sm" onClick={p.onCheck} disabled={p.checking}>
            {t("geometry:tools.check")}
          </Button>
          {tb.dirty ? <span className={styles.unsaved}>{t("geometry:tools.unsaved")}</span> : null}
          <Button size="sm" onClick={p.onSave} disabled={!tb.dirty || p.saving}>
            {p.saving ? t("geometry:tools.saving") : t("geometry:tools.save")}
          </Button>
        </div>
      ) : null}
    </div>
  );
}
