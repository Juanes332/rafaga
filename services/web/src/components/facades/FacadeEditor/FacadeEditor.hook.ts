import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import {
  facadeStrategiesQueryOptions,
  useCreateFacadeElement,
  useDeleteFacadeElement,
  useUpdateFacadeElement,
} from "@/api/facades/facades.queries";
import type { Adjustment, FacadeElementWithAdjustments, FacadeStrategy, StrategyType } from "@/types/facades/facade.types";
import type { FacadeEditorProps, ParamView } from "./FacadeEditor.types";
import { adjustmentMessages, defaultParams, paramViews } from "./FacadeEditor.utils";

export interface UseFacadeEditor {
  strategies: FacadeStrategy[];
  type: StrategyType;
  params: ParamView[];
  adjustments: string[];
  pending: boolean;
  error: unknown;
  setType: (t: StrategyType) => void;
  onParam: (key: string, value: number) => void;
  onApply: () => void;
  onRemove: () => void;
}

function useFacadeMutations(p: FacadeEditorProps) {
  const create = useCreateFacadeElement(p.projectId, p.alternativeId);
  const update = useUpdateFacadeElement(p.projectId, p.alternativeId);
  const remove = useDeleteFacadeElement(p.projectId, p.alternativeId);
  return {
    create,
    update,
    remove,
    pending: create.isPending || update.isPending || remove.isPending,
    error: create.error ?? update.error ?? remove.error,
  };
}

/** Draft params for a new strategy; direct PATCH for an existing one. Clamps come back as adjustments. */
export function useFacadeEditor(p: FacadeEditorProps): UseFacadeEditor {
  const { t } = useTranslation();
  const strategies = useQuery(facadeStrategiesQueryOptions()).data ?? [];
  const [type, setType] = useState<StrategyType>(p.element?.type ?? "screen");
  const [draft, setDraft] = useState<Record<string, number | null>>({});
  const [adjustments, setAdjustments] = useState<Adjustment[]>([]);
  const m = useFacadeMutations(p);
  const strategy = strategies.find((s) => s.type === type);
  useEffect(() => setType(p.element?.type ?? "screen"), [p.element?.type, p.edge.buildingId, p.edge.edgeIndex]);
  useEffect(() => {
    setDraft(defaultParams(strategy));
    setAdjustments([]);
  }, [strategy, p.edge.buildingId, p.edge.edgeIndex]);
  const values = p.element ? (p.element.params as Record<string, number | null>) : draft;
  const done = (res: FacadeElementWithAdjustments) => setAdjustments(res.adjustments);
  const el = p.element;
  return {
    strategies,
    type,
    params: paramViews(strategy, values, t),
    adjustments: adjustmentMessages(adjustments, t),
    pending: m.pending,
    error: m.error,
    setType,
    onParam: (key, value) =>
      el ? m.update.mutate({ id: el.id, params: { [key]: value } }, { onSuccess: done }) : setDraft((d) => ({ ...d, [key]: value })),
    onApply: () =>
      m.create.mutate(
        { building_id: p.edge.buildingId, edge_index: p.edge.edgeIndex, type, params: draft },
        { onSuccess: (res) => (done(res), toast(t("alternatives:editor.applied"))) },
      ),
    onRemove: () => el && m.remove.mutate(el.id, { onSuccess: () => toast(t("alternatives:editor.removed")) }),
  };
}
