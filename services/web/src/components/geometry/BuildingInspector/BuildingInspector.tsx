import { useTranslation } from "react-i18next";
import { ParamField } from "@/components/forms/ParamField/ParamField";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { DEFAULT_HEIGHT_M, HEIGHT_RANGE } from "@/engines/geometry/buildings";
import { useBuildingInspector } from "./BuildingInspector.hook";
import styles from "./BuildingInspector.module.css";

/** Selected building: name, height, footprint facts, scale and delete. */
export function BuildingInspector({ readOnly }: { readOnly: boolean }) {
  const { t } = useTranslation();
  const b = useBuildingInspector();
  if (!b.building) return null;
  return (
    <section className={styles.root} aria-labelledby="building-title">
      <h2 id="building-title" className={styles.title}>
        {b.building.name ?? t("geometry:canvas.unnamed")}
      </h2>
      <div className={styles.field}>
        <Label htmlFor="building-name">{t("geometry:inspector.name")}</Label>
        <Input
          key={b.building.id}
          id="building-name"
          defaultValue={b.building.name ?? ""}
          disabled={readOnly}
          onBlur={(e) => b.onName(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && b.onName(e.currentTarget.value)}
        />
      </div>
      <ParamField
        id="building-height"
        label={t("geometry:inspector.height")}
        value={b.building.height_m}
        unit="m"
        min={HEIGHT_RANGE[0]}
        max={HEIGHT_RANGE[1]}
        step={0.5}
        decimals={1}
        defaultValue={DEFAULT_HEIGHT_M}
        help={t("geometry:inspector.heightHelp")}
        slider
        disabled={readOnly}
        onCommit={b.onHeight}
      />
      <dl className={styles.facts}>
        <div>
          <dt>{t("geometry:inspector.area")}</dt>
          <dd className="num">{b.areaText}</dd>
        </div>
        <div>
          <dt>{t("geometry:inspector.source")}</dt>
          <dd>{b.sourceText}</dd>
        </div>
      </dl>
      {!readOnly ? (
        <div className={styles.actions}>
          <Button variant="outline" size="sm" onClick={b.onShrink}>
            {t("geometry:inspector.shrink")}
          </Button>
          <Button variant="outline" size="sm" onClick={b.onGrow}>
            {t("geometry:inspector.grow")}
          </Button>
          <Button variant="ghost" size="sm" className={styles.delete} onClick={b.onDelete}>
            {t("geometry:inspector.delete")}
          </Button>
        </div>
      ) : null}
    </section>
  );
}
