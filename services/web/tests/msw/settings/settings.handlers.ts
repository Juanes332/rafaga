import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { errorBody, registerReset } from "../mock-state";
import type { Settings, SettingsPatch } from "@/types/settings/settings.types";

export function defaultSettings(): Settings {
  return {
    thresholds: { k_accel: 1.2, k_stagnation: 0.3, dk_reduction: -0.1 },
    lawson: {
      exceedance_probability: 0.05,
      comfort: [
        { key: "A", label_key: "lawson.sitting", threshold_ms: 4 },
        { key: "B", label_key: "lawson.standing", threshold_ms: 6 },
        { key: "C", label_key: "lawson.strolling", threshold_ms: 8 },
        { key: "D", label_key: "lawson.business", threshold_ms: 10 },
        { key: "E", label_key: "lawson.uncomfortable", threshold_ms: null },
      ],
      safety_probability: 0.00025,
      safety: [
        { key: "S15", label_key: "lawson.safety15", threshold_ms: 15 },
        { key: "S20", label_key: "lawson.safety20", threshold_ms: 20 },
      ],
    },
    turbulence_intensity_default: 0.25,
    vegetation_cd: 0.2,
    alternatives_limit: 8,
  };
}

export const settingsState = { settings: defaultSettings(), patches: [] as SettingsPatch[] };
registerReset(() => {
  settingsState.settings = defaultSettings();
  settingsState.patches = [];
});

/** MSW handlers for the settings domain. */
export const settingsHandlers: HttpHandler[] = [
  http.get(`${API}/settings`, () => HttpResponse.json(settingsState.settings)),
  http.patch(`${API}/settings`, async ({ request }) => {
    const patch = (await request.json()) as SettingsPatch;
    settingsState.patches.push(patch);
    if (patch.alternatives_limit !== undefined && patch.alternatives_limit > 20) {
      return HttpResponse.json(errorBody("validation_error", "x", { errors: [{ loc: ["body", "alternatives_limit"], type: "less_than_equal" }] }), {
        status: 422,
      });
    }
    const t = patch.thresholds;
    if (t && t.k_stagnation >= t.k_accel) return HttpResponse.json(errorBody("invalid_thresholds"), { status: 422 });
    settingsState.settings = { ...settingsState.settings, ...patch } as Settings;
    return HttpResponse.json(settingsState.settings);
  }),
];
