import { useTranslation } from "react-i18next";
import { FieldRaster } from "@/components/results/FieldRaster/FieldRaster";
import { KLegend } from "@/components/results/KLegend/KLegend";
import { PlanOverlay } from "@/components/results/PlanOverlay/PlanOverlay";
import { ZoneOverlay } from "@/components/results/ZoneOverlay/ZoneOverlay";
import { balanceColor, kColor } from "@/engines/colormaps/colormap";
import { formatNumber } from "@/lib/format/format.number";
import { useCompareStage } from "./CompareStage.hook";
import type { CompareStageProps } from "./CompareStage.types";
import styles from "./CompareStage.module.css";

/** Before/after swipe of two K fields on the common grid, or the ΔK map. */
export function CompareStage(p: CompareStageProps) {
  const { t } = useTranslation();
  const s = useCompareStage(p);
  const layer = { view: s.view, width: s.size.width, height: s.size.height, className: styles.layer };
  const zoneLayer = (codes: Uint8Array | null) =>
    codes ? <ZoneOverlay {...layer} codes={codes} cols={p.a.cols} rows={p.a.rows} colors={s.colors} /> : null;
  const overlay = (
    <svg className={styles.layer} width={s.size.width} height={s.size.height} aria-hidden>
      <PlanOverlay view={s.view} grid={p.grid} buildings={p.buildings} labels={[]} section={[]} />
    </svg>
  );
  const clip = s.vertical ? `inset(${s.slider.position}% 0 0 0)` : `inset(0 0 0 ${s.slider.position}%)`;
  return (
    <div className={styles.root}>
      <div ref={s.box} className={styles.stage} onPointerMove={s.onPointerMove} onPointerLeave={s.onPointerLeave}>
        {s.dk ? (
          <>
            <FieldRaster {...layer} field={s.dk} color={balanceColor} alpha={235} />
            {zoneLayer(s.codes.b)}
            {overlay}
          </>
        ) : (
          <>
            <FieldRaster {...layer} field={p.a} color={kColor} alpha={235} />
            {zoneLayer(s.codes.a)}
            <div className={styles.clipB} style={{ clipPath: clip }}>
              <FieldRaster {...layer} field={p.b} color={kColor} alpha={235} />
              {zoneLayer(s.codes.b)}
            </div>
            {overlay}
            <span className={styles.tagA}>{`${t("compare:a")}  ${p.labelA}`}</span>
            <span className={styles.tagB}>{`${p.labelB}  ${t("compare:b")}`}</span>
            <div
              role="slider"
              tabIndex={0}
              aria-label={t("compare:slider")}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={Math.round(s.slider.position)}
              aria-valuetext={`${Math.round(s.slider.position)} %`}
              aria-orientation={s.vertical ? "vertical" : "horizontal"}
              className={s.vertical ? styles.handleH : styles.handleV}
              style={s.vertical ? { top: `${s.slider.position}%` } : { left: `${s.slider.position}%` }}
              onKeyDown={s.slider.onKeyDown}
              onPointerDown={s.slider.onPointerDown}
              onPointerMove={s.slider.onPointerMove}
              onPointerUp={s.slider.onPointerUp}
            >
              <span className={styles.grip} aria-hidden />
            </div>
          </>
        )}
      </div>
      <div className={styles.footer}>
        <KLegend kind={s.dk ? "dk" : "k"} marks={s.dk ? [p.thresholds.dk_reduction] : [p.thresholds.k_stagnation, p.thresholds.k_accel]} />
        <output className={styles.readout} aria-live="off">
          {s.readout ? (
            s.dk ? (
              <span>{`${t("compare:readoutDk")} ${formatNumber(s.readout.b - s.readout.a, 2)}`}</span>
            ) : (
              <>
                <span>{`${t("compare:readoutA")} ${formatNumber(s.readout.a, 2)}`}</span>
                <span>{`${t("compare:readoutB")} ${formatNumber(s.readout.b, 2)}`}</span>
              </>
            )
          ) : null}
        </output>
      </div>
    </div>
  );
}
