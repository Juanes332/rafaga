import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { toast } from "sonner";
import { useShallow } from "zustand/react/shallow";
import { estimateQueryOptions, useCreateSimulation } from "@/api/simulations/simulations.queries";
import { isSolverOffline, needsCpuConfirmation } from "@/components/simulations/CpuWarningDialog/CpuWarningDialog.utils";
import { useSimulationFormStore } from "@/stores/simulations/simulations.store";
import type { EstimateRequest } from "@/types/simulations/simulation.types";
import type { SimulationFormProps } from "./SimulationForm.types";

/** Builds the request from the shared form store, estimates it live and launches it. */
export function useSimulationForm({ projectId, alternatives }: SimulationFormProps) {
  const { t } = useTranslation();
  const f = useSimulationFormStore(useShallow((s) => s));
  const [missingDirection, setMissingDirection] = useState(false);
  const alternativeId = f.alternativeId && alternatives.some((a) => a.id === f.alternativeId) ? f.alternativeId : (alternatives[0]?.id ?? null);
  const section = f.kind === "section2d";
  const request: EstimateRequest = { alternative_id: alternativeId ?? "", kind: f.kind, directions_deg: f.directions, dx_m: f.dxM, device: f.device };
  const ready = Boolean(alternativeId) && !section && f.directions.length > 0;
  const estimate = useQuery(estimateQueryOptions(request, ready));
  const create = useCreateSimulation(projectId);

  const solverOffline = ready && isSolverOffline(estimate.data);
  const [confirmingCpu, setConfirmingCpu] = useState(false);
  const launch = () => create.mutate({ ...request, auto_coarsen: f.autoCoarsen }, { onSuccess: () => toast(t("simulate:form.launched")) });
  const onLaunch = () => {
    if (solverOffline) return;
    if (f.directions.length === 0) return setMissingDirection(true);
    setMissingDirection(false);
    if (needsCpuConfirmation(f.kind, ready ? estimate.data : undefined)) return setConfirmingCpu(true);
    launch();
  };
  const onConfirmCpu = () => {
    setConfirmingCpu(false);
    launch();
  };
  return {
    f,
    alternativeId,
    section,
    estimate: ready ? estimate.data : undefined,
    estimating: estimate.isFetching,
    estimateError: estimate.error,
    launchError: create.error,
    missingDirection: missingDirection && f.directions.length === 0,
    pending: create.isPending,
    solverOffline,
    onLaunch,
    confirmingCpu,
    onConfirmCpu,
    onCancelCpu: () => setConfirmingCpu(false),
  };
}
