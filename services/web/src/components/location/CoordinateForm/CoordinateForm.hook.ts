import { useEffect, useState, type FormEvent } from "react";
import { formatCoord } from "@/lib/format/format.number";
import { parseCoordPair, parseCoords } from "./CoordinateForm.utils";

interface CoordinateFormInput {
  lat: number | null;
  lon: number | null;
  onSubmit: (lat: number, lon: number) => void;
}

interface UseCoordinateForm {
  latText: string;
  lonText: string;
  invalid: boolean;
  setLat: (v: string) => void;
  setLon: (v: string) => void;
  submit: (e: FormEvent) => void;
}

/** Draft coordinates, resynced when the project location changes. */
export function useCoordinateForm({ lat, lon, onSubmit }: CoordinateFormInput): UseCoordinateForm {
  const [latText, setLat] = useState(lat == null ? "" : formatCoord(lat));
  const [lonText, setLon] = useState(lon == null ? "" : formatCoord(lon));
  const [invalid, setInvalid] = useState(false);
  useEffect(() => {
    if (lat != null) setLat(formatCoord(lat));
    if (lon != null) setLon(formatCoord(lon));
  }, [lat, lon]);
  return {
    latText,
    lonText,
    invalid,
    setLat,
    setLon,
    submit: (e) => {
      e.preventDefault();
      // A whole position pasted in Latitud is split by its hemisphere letters.
      const c = lonText.trim() === "" ? parseCoordPair(latText) : parseCoords(latText, lonText);
      setInvalid(c === null);
      if (c) onSubmit(c.lat, c.lon);
    },
  };
}
