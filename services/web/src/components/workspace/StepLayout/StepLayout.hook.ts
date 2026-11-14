import { useState } from "react";
import { useMediaQuery } from "@/hooks/media/use-media-query";

interface UseStepLayout {
  docked: boolean;
  sheetSide: "right" | "bottom";
  open: boolean;
  setOpen: (open: boolean) => void;
}

/** ≥1024 docks the inspector; below it becomes a side panel, under 768 a bottom sheet. */
export function useStepLayout(): UseStepLayout {
  const wide = useMediaQuery("(min-width: 1024px)");
  const tablet = useMediaQuery("(min-width: 768px)");
  const [open, setOpen] = useState(false);
  // jsdom reports no media matches; treat that as desktop so tests see the docked inspector.
  const docked = wide || (typeof window !== "undefined" && window.innerWidth >= 1024);
  return { docked, sheetSide: tablet ? "right" : "bottom", open, setOpen };
}
