import { useShallow } from "zustand/react/shallow";
import { useTranslation } from "react-i18next";
import { coverage, dominantDirections } from "@/components/wind/WindRose/WindRose.utils";
import { formatPercent } from "@/lib/format/format.number";
import { useSimulationFormStore } from "@/stores/simulations/simulations.store";
import type { WindSector } from "@/types/wind/wind.types";

interface UseDirectionPicker {
  selected: number[];
  countText: string;
  coverageText: string;
  toggle: (deg: number) => void;
  pickDominant: (() => void) | null;
  clear: () => void;
}

/** 1–16 directions; coverage = share of time the chosen sectors blow. */
export function useDirectionPicker(sectors: WindSector[] | null): UseDirectionPicker {
  const { t } = useTranslation();
  const { selected, toggle, setDirections } = useSimulationFormStore(
    useShallow((s) => ({ selected: s.directions, toggle: s.toggleDirection, setDirections: s.setDirections })),
  );
  const cov = coverage(sectors, selected);
  return {
    selected,
    countText: t("simulate:form.directionsCount", { count: selected.length }),
    coverageText: selected.length === 0 ? "" : cov === null ? t("simulate:form.noRose") : t("simulate:form.coverage", { value: formatPercent(cov) }),
    toggle,
    pickDominant: sectors?.length ? () => setDirections(dominantDirections(sectors, 0.6)) : null,
    clear: () => setDirections([]),
  };
}
