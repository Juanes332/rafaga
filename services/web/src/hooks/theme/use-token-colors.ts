import { useMemo } from "react";
import { useMediaQuery } from "@/hooks/media/use-media-query";
import { useThemeStore } from "@/stores/theme/theme.store";

export interface TokenColors {
  ink: string;
  ground: string;
  accel: string;
  stagnation: string;
  reduction: string;
  danger: string;
}

const NAMES: Record<keyof TokenColors, string> = {
  ink: "--color-ink",
  ground: "--color-ground",
  accel: "--color-zone-accel",
  stagnation: "--color-zone-stagnation",
  reduction: "--color-zone-reduction",
  danger: "--color-danger",
};

/** Design tokens resolved for canvases, which cannot read CSS variables; follows theme changes. */
export function useTokenColors(): TokenColors {
  const theme = useThemeStore((s) => s.theme);
  const dark = useMediaQuery("(prefers-color-scheme: dark)");
  return useMemo(() => {
    const style = getComputedStyle(document.documentElement);
    const out = {} as TokenColors;
    for (const [k, v] of Object.entries(NAMES)) out[k as keyof TokenColors] = style.getPropertyValue(v).trim() || "#1e2a30";
    return out;
    // theme/dark are the invalidation keys: the values come from the DOM.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [theme, dark]);
}

/** "#rrggbb" or "rgb(…)" → [r, g, b, a] in 0..1 for WebGL. */
export function cssToRgba(css: string, alpha: number): [number, number, number, number] {
  const hex = css.match(/^#([0-9a-f]{6})$/i);
  if (hex) {
    const n = parseInt(hex[1], 16);
    return [((n >> 16) & 255) / 255, ((n >> 8) & 255) / 255, (n & 255) / 255, alpha];
  }
  const nums = css.match(/[\d.]+/g)?.map(Number) ?? [30, 42, 48];
  return [nums[0] / 255, nums[1] / 255, nums[2] / 255, alpha];
}
