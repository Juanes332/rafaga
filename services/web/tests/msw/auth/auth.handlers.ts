import { http, HttpResponse } from "msw";
import { API } from "../api-base";
import { errorBody, registerReset } from "../mock-state";
import type { Token, User } from "@/types/auth/auth.types";

export const architect: User = { id: "00000000-0000-4000-8000-0000000000a1", email: "ana@estudio.co", role: "architect" };
export const authState = { needsSetup: false, user: architect as User };
registerReset(() => {
  authState.needsSetup = false;
  authState.user = architect;
});

export function tokenFor(user: User): Token {
  return { access_token: `token-${user.id}`, token_type: "bearer", expires_in: 43200, user };
}

export const authHandlers = [
  http.get(`${API}/auth/setup-status`, () => HttpResponse.json({ needs_setup: authState.needsSetup })),
  http.post(`${API}/auth/setup`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string };
    if (!authState.needsSetup) return HttpResponse.json(errorBody("setup_already_done"), { status: 409 });
    if (body.password.length < 10) return HttpResponse.json(errorBody("password_too_short"), { status: 422 });
    authState.needsSetup = false;
    authState.user = { ...architect, email: body.email };
    return HttpResponse.json(tokenFor(authState.user), { status: 201 });
  }),
  http.post(`${API}/auth/login`, async ({ request }) => {
    const body = (await request.json()) as { email: string; password: string };
    if (body.password === "demasiados") {
      return HttpResponse.json(errorBody("rate_limited"), { status: 429, headers: { "Retry-After": "37" } });
    }
    if (body.password !== "contrasena-segura") return HttpResponse.json(errorBody("invalid_credentials"), { status: 401 });
    return HttpResponse.json(tokenFor({ ...authState.user, email: body.email }));
  }),
  http.get(`${API}/auth/me`, () => HttpResponse.json(authState.user)),
];
