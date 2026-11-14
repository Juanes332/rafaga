import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { GpsButton } from "@/components/location/GpsButton/GpsButton";
import { useCoordinateForm } from "./CoordinateForm.hook";
import styles from "./CoordinateForm.module.css";

interface CoordinateFormProps {
  lat: number | null;
  lon: number | null;
  pending: boolean;
  onSubmit: (lat: number, lon: number) => void;
}

/** Typed latitude/longitude (decimal, DMS or DDM) or the device GPS. */
export function CoordinateForm(props: CoordinateFormProps) {
  const { t } = useTranslation();
  const f = useCoordinateForm(props);
  return (
    <form className={styles.root} onSubmit={f.submit} aria-labelledby="coords-title" noValidate>
      <h2 id="coords-title" className={styles.title}>
        {t("location:coords.title")}
      </h2>
      <GpsButton disabled={props.pending} onFix={props.onSubmit} />
      <div className={styles.pair}>
        <div className={styles.field}>
          <Label htmlFor="lat">{t("location:coords.lat")}</Label>
          <Input id="lat" inputMode="text" autoComplete="off" aria-describedby="coords-hint" value={f.latText} aria-invalid={f.invalid || undefined} onChange={(e) => f.setLat(e.target.value)} />
        </div>
        <div className={styles.field}>
          <Label htmlFor="lon">{t("location:coords.lon")}</Label>
          <Input id="lon" inputMode="text" autoComplete="off" aria-describedby="coords-hint" value={f.lonText} aria-invalid={f.invalid || undefined} onChange={(e) => f.setLon(e.target.value)} />
        </div>
      </div>
      <p id="coords-hint" className={styles.hint}>
        {t("location:coords.hint")}
      </p>
      {f.invalid ? <p className={styles.error} role="alert">{t("location:coords.invalid")}</p> : null}
      <Button type="submit" variant="secondary" disabled={props.pending} className={styles.submit}>
        {props.pending ? t("location:coords.submitting") : t("location:coords.submit")}
      </Button>
    </form>
  );
}
