import { useTranslation } from "react-i18next";
import { ErrorNotice } from "@/components/feedback/ErrorNotice/ErrorNotice";
import { Command, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { formatCoord } from "@/lib/format/format.number";
import { usePlaceSearch } from "./PlaceSearch.hook";
import styles from "./PlaceSearch.module.css";

/** Place search (GET /geo/search): choosing a result fixes the location. */
export function PlaceSearch({ onPick }: { onPick: (lat: number, lon: number) => void }) {
  const { t } = useTranslation();
  const s = usePlaceSearch();
  return (
    <div className={styles.root}>
      {/* cmdk labels the input itself (sr-only); this is the visible twin. */}
      <span className={styles.label} aria-hidden>
        {t("location:search.label")}
      </span>
      <Command shouldFilter={false} label={t("location:search.label")}>
        <CommandInput value={s.text} onValueChange={s.setText} placeholder={t("location:search.placeholder")} />
        <CommandList>
          {s.results.map((r) => (
            <CommandItem key={`${r.lat},${r.lon}`} value={`${r.name}-${r.lat}-${r.lon}`} onSelect={() => (onPick(r.lat, r.lon), s.setText(""))}>
              <span className={styles.name}>{r.name}</span>
              <span className={styles.meta}>
                {[r.admin1, r.country].filter(Boolean).join(", ")} {`${formatCoord(r.lat)}, ${formatCoord(r.lon)}`}
              </span>
            </CommandItem>
          ))}
        </CommandList>
      </Command>
      {s.tooShort ? <p className={styles.hint}>{t("location:search.hint")}</p> : null}
      {s.searching ? <p className={styles.hint}>{t("location:search.searching")}</p> : null}
      {s.empty ? <p className={styles.hint}>{t("location:search.empty")}</p> : null}
      {s.error ? <ErrorNotice error={s.error} /> : null}
    </div>
  );
}
