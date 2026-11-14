import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { systemStatusQueryOptions } from "@/api/system/system.queries";
import type { TFunction } from "i18next";
import type { SystemStatus } from "@/types/system/system.types";

export interface ServiceRow {
  key: "api" | "db" | "solver";
  ok: boolean;
}

interface UseComputeBadge {
  label: string;
  healthy: boolean;
  healthLabel: string;
  services: ServiceRow[];
  cpuOnly: boolean;
}

export function deviceLabel(status: SystemStatus | undefined, t: TFunction): string {
  const s = status?.solver;
  if (!s || !s.online) return t("common:compute.offline");
  if (s.device === "gpu" && s.gpu_name) return t("common:compute.gpu", { name: s.gpu_name });
  return s.cpu_cores ? t("common:compute.cpu", { cores: s.cpu_cores }) : t("common:compute.cpuUnknown");
}

/** "GPU: <model>" or "CPU: N núcleos" plus a health dot from GET /system/status. */
export function useComputeBadge(): UseComputeBadge {
  const { t } = useTranslation();
  const { data, isError } = useQuery(systemStatusQueryOptions());
  const services: ServiceRow[] = [
    { key: "api", ok: !isError && data?.api === "ok" },
    { key: "db", ok: data?.db === "ok" },
    { key: "solver", ok: Boolean(data?.solver.online) },
  ];
  const healthy = services.every((s) => s.ok);
  return {
    label: isError ? t("common:compute.offline") : deviceLabel(data, t),
    healthy,
    healthLabel: healthy ? t("common:compute.healthy") : t("common:compute.unhealthy"),
    services,
    cpuOnly: data?.solver.online === true && data.solver.device === "cpu",
  };
}
