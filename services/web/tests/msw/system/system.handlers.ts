import { http, HttpResponse } from "msw";
import { API } from "../api-base";
import { registerReset } from "../mock-state";
import type { SystemStatus } from "@/types/system/system.types";

export const gpuStatus: SystemStatus = {
  api: "ok",
  db: "ok",
  solver: {
    online: true,
    device: "gpu",
    gpu_name: "NVIDIA RTX 4060",
    vram_total_bytes: 8_589_934_592,
    ram_budget_bytes: 19_327_352_832,
    cpu_cores: 16,
    mlups_2d: 1800,
    mlups_3d: 420,
    heartbeat_at: "2026-11-13T12:00:00Z",
  },
};

export const systemState = { status: gpuStatus };
registerReset(() => {
  systemState.status = gpuStatus;
});

export const systemHandlers = [http.get(`${API}/system/status`, () => HttpResponse.json(systemState.status))];
