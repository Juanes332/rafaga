import type { WindSector } from "@/types/wind/wind.types";

export interface WindRoseProps {
  sectors: WindSector[] | null;
  /** Rendered size in px (square). */
  size?: number;
  /** Selection mode (SCR-12): each sector is a keyboard-operable checkbox. */
  selected?: number[];
  onToggle?: (deg: number) => void;
  /** Manual wind: a single arrow from this bearing. */
  manualDeg?: number | null;
}
