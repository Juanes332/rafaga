import { LocateFixed } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { useGpsButton } from "./GpsButton.hook";
import styles from "./GpsButton.module.css";

interface GpsButtonProps {
  disabled: boolean;
  onFix: (lat: number, lon: number) => void;
}

/** Fixes the project location from the device GPS and reports accuracy or why it failed. */
export function GpsButton({ disabled, onFix }: GpsButtonProps) {
  const { t } = useTranslation();
  const g = useGpsButton(onFix);
  return (
    <div className={styles.root}>
      <Button type="button" variant="secondary" disabled={disabled || g.locating} onClick={g.locate}>
        <LocateFixed aria-hidden />
        {g.locating ? t("location:coords.gps.locating") : t("location:coords.gps.button")}
      </Button>
      {/* Live region stays mounted so the first accuracy message is announced. */}
      <p role="status" className={styles.note}>
        {g.error ? null : g.message}
      </p>
      {g.error ? (
        <p role="alert" className={styles.error}>
          {g.message}
        </p>
      ) : null}
    </div>
  );
}
