import { useTranslation } from "react-i18next";
import { CompassRose } from "@/components/orientation/CompassRose/CompassRose";
import { useLocationMap } from "./LocationMap.hook";
import type { LocationMapProps } from "./LocationMap.types";
import { ATTRIBUTION } from "./LocationMap.adapter";
import styles from "./LocationMap.module.css";

/** OSM map through the api proxy; a neutral metric grid shows when tiles or WebGL are missing. */
export function LocationMap(props: LocationMapProps) {
  const { t } = useTranslation();
  const m = useLocationMap(props);
  return (
    <div className={styles.root}>
      {m.status !== "unsupported" ? (
        <div ref={m.container} className={styles.map} role="application" aria-label={t("location:map.label")} />
      ) : null}
      {/* MapLibre keeps the map north-up, so the rose never rotates. */}
      <CompassRose className={styles.compass} size={104} />
      {m.status === "offline" ? <p className={styles.notice}>{t("location:map.offline")}</p> : null}
      {m.status === "unsupported" ? (
        <>
          <p className={styles.notice}>{t("location:map.noWebgl")}</p>
          <p className={styles.attribution}>{ATTRIBUTION}</p>
        </>
      ) : null}
    </div>
  );
}
