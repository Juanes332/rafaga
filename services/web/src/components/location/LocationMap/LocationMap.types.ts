export interface LocationMapProps {
  lat: number | null;
  lon: number | null;
  onPick: (lat: number, lon: number) => void;
}

export type MapStatus = "loading" | "ready" | "offline" | "unsupported";
