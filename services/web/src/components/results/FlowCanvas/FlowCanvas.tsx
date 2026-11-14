import { Maximize, Minus, Pause, Play, Plus } from "lucide-react";
import { useTranslation } from "react-i18next";
import { FieldRaster } from "@/components/results/FieldRaster/FieldRaster";
import { ParticleLayer } from "@/components/results/ParticleLayer/ParticleLayer";
import { StreamlinesLayer } from "@/components/results/StreamlinesLayer/StreamlinesLayer";
import { ZoneOverlay } from "@/components/results/ZoneOverlay/ZoneOverlay";
import { CompassRose } from "@/components/orientation/CompassRose/CompassRose";
import { Button } from "@/components/ui/button";
import { formatUnit } from "@/lib/format/format.number";
import { useFlowCanvas } from "./FlowCanvas.hook";
import type { FlowCanvasProps } from "./FlowCanvas.types";
import styles from "./FlowCanvas.module.css";

/** K field + animated particles (or static streamlines) + zones + overlay, with readout and controls. */
export function FlowCanvas(p: FlowCanvasProps) {
  const { t } = useTranslation();
  const f = useFlowCanvas(p);
  const layer = { view: f.view, width: f.size.width, height: f.size.height, className: styles.layer };
  return (
    <div className={styles.root}>
      <div
        ref={f.box}
        className={styles.stage}
        tabIndex={0}
        role="img"
        aria-label={t("results:flow.label")}
        aria-describedby="flow-pause-hint"
        onWheel={f.onWheel}
        onPointerDown={f.onPointerDown}
        onPointerMove={f.onPointerMove}
        onPointerUp={f.onPointerUp}
        onPointerLeave={f.onPointerLeave}
        onKeyDown={f.onKeyDown}
      >
        <FieldRaster {...layer} field={p.paint} color={p.paintColor} alpha={217} />
        {p.zoneCodes ? <ZoneOverlay {...layer} codes={p.zoneCodes} cols={p.K.cols} rows={p.K.rows} colors={f.colors} /> : null}
        {f.staticMode || !p.velocity ? (
          <StreamlinesLayer {...layer} lines={f.lines} rows={p.K.rows} />
        ) : (
          <ParticleLayer {...layer} data={p.velocity} cols={p.K.cols} rows={p.K.rows} paused={p.paused} ink={f.colors.ink} onUnavailable={f.onUnavailable} />
        )}
        {p.overlay ? (
          <svg className={styles.layer} width={f.size.width} height={f.size.height}>
            {p.overlay(f.view)}
          </svg>
        ) : null}
        {f.readout ? (
          <output className={styles.readout} style={{ left: f.readout.x + 14, top: f.readout.y + 14 }}>
            {f.readout.text}
          </output>
        ) : null}
      </div>
      <div className={styles.bottomLeft}>{p.legend}</div>
      <div className={styles.bottomRight}>
        {f.staticMode ? (
          <p className={styles.note}>{f.staticLabel}</p>
        ) : (
          <Button variant="secondary" size="sm" onClick={p.onTogglePause} aria-pressed={p.paused}>
            {p.paused ? <Play aria-hidden /> : <Pause aria-hidden />}
            {p.paused ? t("results:flow.resume") : t("results:flow.pause")}
          </Button>
        )}
        <span id="flow-pause-hint" className="sr-only">
          {t("results:flow.pauseHint")}
        </span>
        {/* The flow grid is drawn north-up, like the plan. */}
        <CompassRose className={styles.north} size={104} />
        <span className={styles.scale} role="img" aria-label={`${t("results:flow.scale")} ${formatUnit(f.scale.metres, 0, "m")}`}>
          <span className={styles.scaleBar} style={{ width: f.scale.px }} />
          {formatUnit(f.scale.metres, 0, "m")}
        </span>
      </div>
      <div className={styles.zoom}>
        <Button variant="secondary" size="icon" aria-label={t("results:flow.zoomIn")} onClick={() => f.zoomBy(1.4)}>
          <Plus aria-hidden />
        </Button>
        <Button variant="secondary" size="icon" aria-label={t("results:flow.zoomOut")} onClick={() => f.zoomBy(1 / 1.4)}>
          <Minus aria-hidden />
        </Button>
        <Button variant="secondary" size="icon" aria-label={t("results:flow.fit")} onClick={f.fit}>
          <Maximize aria-hidden />
        </Button>
      </div>
    </div>
  );
}
