import { lazy, Suspense } from "react";
import { useTranslation } from "react-i18next";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useGeometry3D } from "./Geometry3D.hook";
import styles from "./Geometry3D.module.css";

// three.js + r3f load only when the 3D view opens (ADR-21 code splitting).
const Geometry3DView = lazy(() => import("@/components/geometry/Geometry3DView/Geometry3DView").then((m) => ({ default: m.Geometry3DView })));

/** SCR-09: orbitable 3D view of the base buildings and an alternative's façade elements. */
export function Geometry3D({ projectId }: { projectId: string }) {
  const { t } = useTranslation();
  const v = useGeometry3D(projectId);
  if (!v.webgl) return <p className={styles.message}>{t("geometry:view3d.noWebgl")}</p>;
  return (
    <div className={styles.root}>
      <Suspense fallback={<p className={styles.message}>{t("geometry:view3d.loading")}</p>}>
        <Geometry3DView alternativeId={v.alternativeId} label={t("geometry:view3d.label")} />
      </Suspense>
      <div className={styles.panel}>
        {v.alternatives.length > 1 ? (
          <div className={styles.field}>
            <Label htmlFor="alt-3d">{t("geometry:view3d.alternative")}</Label>
            <Select value={v.alternativeId ?? undefined} onValueChange={v.setAlternative}>
              <SelectTrigger id="alt-3d" className={styles.select}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {v.alternatives.map((a) => (
                  <SelectItem key={a.id} value={a.id}>
                    {a.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ) : null}
        <ul className={styles.legend}>
          <li>
            <span className={styles.swatchBuilding} aria-hidden /> {t("geometry:view3d.legendBuilding")}
          </li>
          <li>
            <span className={styles.swatchElement} aria-hidden /> {t("geometry:view3d.legendElement")}
          </li>
          <li>
            <span className={styles.swatchPorous} aria-hidden /> {t("geometry:view3d.legendPorous")}
          </li>
        </ul>
      </div>
    </div>
  );
}
