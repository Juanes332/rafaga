import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { errorBody, registerReset } from "../mock-state";
import type { BackgroundPlan } from "@/types/geometry/geometry.types";

// 1×1 grey PNG: enough for <img> and blob URLs in tests and mock mode.
const PNG = Uint8Array.from(
  atob("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mN89+7dfwAJjwPu5YyBTQAAAABJRU5ErkJggg=="),
  (c) => c.charCodeAt(0),
);

export const backgroundsState = { byProject: {} as Record<string, BackgroundPlan[]> };
registerReset(() => {
  backgroundsState.byProject = {};
});

function findPlan(id: string): BackgroundPlan | undefined {
  return Object.values(backgroundsState.byProject).flat().find((b) => b.id === id);
}

/** MSW handlers for the backgrounds (trace plan) domain. */
export const backgroundsHandlers: HttpHandler[] = [
  http.get(`${API}/projects/:id/backgrounds`, ({ params }) => HttpResponse.json(backgroundsState.byProject[String(params.id)] ?? [])),
  http.post(`${API}/projects/:id/backgrounds`, async ({ params, request }) => {
    const file = (await request.formData()).get("file") as File;
    if (!/\.(png|jpe?g|pdf)$/i.test(file.name)) return HttpResponse.json(errorBody("unsupported_format"), { status: 422 });
    const plan: BackgroundPlan = {
      id: `00000000-0000-4000-8000-00000000bg${String((backgroundsState.byProject[String(params.id)]?.length ?? 0) + 1).padStart(2, "0")}`,
      page_count: file.name.toLowerCase().endsWith(".pdf") ? 3 : 1,
      page: 1,
      calibration: null,
      metres_per_pixel: null,
      transform: { offset: [0, 0], rotation_deg: 0, scale: 1 },
      opacity: 0.5,
    };
    backgroundsState.byProject[String(params.id)] = [...(backgroundsState.byProject[String(params.id)] ?? []), plan];
    return HttpResponse.json(plan, { status: 201 });
  }),
  http.get(`${API}/backgrounds/:id/pages/:page`, () => HttpResponse.arrayBuffer(PNG.buffer, { headers: { "Content-Type": "image/png" } })),
  http.patch(`${API}/backgrounds/:id`, async ({ params, request }) => {
    const plan = findPlan(String(params.id));
    if (!plan) return HttpResponse.json(errorBody("background_not_found"), { status: 404 });
    Object.assign(plan, await request.json());
    if (plan.calibration) {
      const { p1, p2, distance_m } = plan.calibration;
      plan.metres_per_pixel = distance_m / Math.hypot(p2[0] - p1[0], p2[1] - p1[1]);
    }
    return HttpResponse.json(plan);
  }),
  http.delete(`${API}/backgrounds/:id`, ({ params }) => {
    for (const k of Object.keys(backgroundsState.byProject)) {
      backgroundsState.byProject[k] = backgroundsState.byProject[k].filter((b) => b.id !== params.id);
    }
    return new HttpResponse(null, { status: 204 });
  }),
];
