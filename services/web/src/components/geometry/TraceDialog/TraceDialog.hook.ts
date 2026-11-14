import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import {
  BACKGROUND_MAX_BYTES,
  backgroundPageQueryOptions,
  backgroundsQueryOptions,
  useUpdateBackground,
  useUploadBackground,
} from "@/api/geometry/backgrounds.queries";
import { formatMegabytes } from "@/components/geometry/ImportDialog/ImportDialog.utils";
import { formatNumber, formatUnit } from "@/lib/format/format.number";
import type { BackgroundPatch } from "@/types/geometry/geometry.types";
import { usePointPair } from "./TraceDialog.points";
import type { TraceDialogProps } from "./TraceDialog.types";

/** Upload → page → calibrate → check with the ruler → opacity. */
export function useTraceDialog({ projectId }: TraceDialogProps) {
  const { t } = useTranslation();
  const list = useQuery(backgroundsQueryOptions(projectId));
  const upload = useUploadBackground(projectId);
  const update = useUpdateBackground(projectId);
  const plan = list.data?.at(-1) ?? null;
  const page = useQuery({ ...backgroundPageQueryOptions(plan?.id ?? "", plan?.page ?? 1), enabled: Boolean(plan) });
  const [sizeError, setSizeError] = useState<string | null>(null);
  const [distance, setDistance] = useState<number | null>(null);
  const pair = usePointPair();
  const calibrated = Boolean(plan?.metres_per_pixel);

  const onFile = (file: File | undefined) => {
    if (!file) return;
    if (file.size > BACKGROUND_MAX_BYTES) return setSizeError(t("geometry:traceDialog.tooLarge", { size: formatMegabytes(file.size) }));
    setSizeError(null);
    upload.mutate(file, { onSuccess: pair.clear });
  };
  const patch = (p: BackgroundPatch) => plan && update.mutate({ id: plan.id, patch: p });
  const calibrate = () => {
    if (pair.points.length !== 2 || !distance) return;
    patch({ calibration: { p1: pair.points[0], p2: pair.points[1], distance_m: distance } });
    pair.clear();
  };
  const ruler = pair.measure(plan?.metres_per_pixel);
  return {
    plan,
    pageUrl: page.data ?? null,
    calibrated,
    points: pair.points,
    onPick: pair.pick,
    distance,
    setDistance,
    calibrate,
    canCalibrate: pair.points.length === 2 && Boolean(distance),
    onFile,
    uploading: upload.isPending,
    error: sizeError ?? upload.error ?? update.error ?? null,
    onPage: (n: number) => (patch({ page: n }), pair.clear()),
    onOpacity: (opacity: number) => patch({ opacity }),
    scaleText: plan?.metres_per_pixel ? t("geometry:traceDialog.calibrated", { value: formatUnit(plan.metres_per_pixel, 4, "m") }) : null,
    rulerText: calibrated && ruler != null ? t("geometry:traceDialog.rulerValue", { value: formatUnit(ruler, 2, "m") }) : null,
    pageLabel: plan ? t("geometry:traceDialog.pageOf", { page: plan.page, count: formatNumber(plan.page_count, 0) }) : "",
  };
}
