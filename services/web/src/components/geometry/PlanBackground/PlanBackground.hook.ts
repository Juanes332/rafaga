import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { backgroundPageQueryOptions, backgroundsQueryOptions } from "@/api/geometry/backgrounds.queries";
import type { BackgroundPlan } from "@/types/geometry/geometry.types";

export interface BackgroundLayer {
  url: string;
  x: number;
  y: number;
  width: number;
  height: number;
  opacity: number;
}

/** Latest calibrated trace plan, placed in metres with its lower-left corner at transform.offset. */
export function usePlanBackground(projectId: string): BackgroundLayer | null {
  const list = useQuery(backgroundsQueryOptions(projectId));
  const plan: BackgroundPlan | undefined = list.data?.filter((b) => b.metres_per_pixel).at(-1);
  const page = useQuery({ ...backgroundPageQueryOptions(plan?.id ?? "", plan?.page ?? 1), enabled: Boolean(plan) });
  const [px, setPx] = useState<[number, number] | null>(null);
  useEffect(() => {
    if (!page.data) return;
    const img = new Image();
    img.onload = () => setPx([img.naturalWidth, img.naturalHeight]);
    img.src = page.data;
  }, [page.data]);
  if (!plan || !page.data || !px || !plan.metres_per_pixel) return null;
  const s = plan.metres_per_pixel * (plan.transform?.scale ?? 1);
  const [ox, oy] = plan.transform?.offset ?? [0, 0];
  const width = px[0] * s;
  const height = px[1] * s;
  return { url: page.data, x: ox, y: -(oy + height), width, height, opacity: plan.opacity ?? 0.5 };
}
