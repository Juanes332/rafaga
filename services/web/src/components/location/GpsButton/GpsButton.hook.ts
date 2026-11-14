import { useTranslation } from "react-i18next";
import { useGeolocation } from "@/hooks/geolocation/use-geolocation";

interface UseGpsButton {
  locating: boolean;
  error: boolean;
  message: string | null;
  locate: () => void;
}

/** Wraps the device fix with Spanish accuracy and failure messages. */
export function useGpsButton(onFix: (lat: number, lon: number) => void): UseGpsButton {
  const { t } = useTranslation();
  const g = useGeolocation((fix) => onFix(fix.lat, fix.lon));
  const message =
    g.error !== null
      ? t(`location:coords.gps.${g.error}`)
      : g.accuracyM !== null
        ? t("location:coords.gps.accuracy", { m: Math.round(g.accuracyM) })
        : null;
  return { locating: g.status === "locating", error: g.error !== null, message, locate: g.locate };
}
