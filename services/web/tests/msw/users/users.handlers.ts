import { http, HttpResponse, type HttpHandler } from "msw";
import { API } from "../api-base";
import { errorBody, mockId, registerReset } from "../mock-state";
import { architect } from "../auth/auth.handlers";
import type { User } from "@/types/auth/auth.types";
import type { Share, UserCreate } from "@/types/users/user.types";

export const reviewer: User = {
  id: "00000000-0000-4000-8000-0000000000a2",
  email: "rev@estudio.co",
  role: "reviewer",
  created_at: "2026-11-11T09:00:00Z",
};

/** Users plus shares keyed by project id. */
export const usersState = { users: [] as User[], shares: {} as Record<string, Share[]> };
registerReset(() => {
  usersState.users = [{ ...architect, created_at: "2026-11-10T09:00:00Z" }, reviewer];
  usersState.shares = {
    "00000000-0000-4000-8000-0000000000p1": [{ user_id: reviewer.id, email: reviewer.email, created_at: "2026-11-12T10:00:00Z" }],
  };
});

async function createUser(request: Request) {
  const body = (await request.json()) as UserCreate;
  if (body.password.length < 10) return HttpResponse.json(errorBody("password_too_short"), { status: 422 });
  if (usersState.users.some((u) => u.email === body.email)) return HttpResponse.json(errorBody("email_taken"), { status: 409 });
  const user: User = { id: mockId("u"), email: body.email, role: body.role, created_at: new Date().toISOString() };
  usersState.users.push(user);
  return HttpResponse.json(user, { status: 201 });
}

/** MSW handlers for users and project shares. */
export const usersHandlers: HttpHandler[] = [
  http.get(`${API}/users`, () => HttpResponse.json(usersState.users)),
  http.post(`${API}/users`, ({ request }) => createUser(request)),
  http.delete(`${API}/users/:id`, ({ params }) => {
    if (params.id === architect.id) return HttpResponse.json(errorBody("cannot_delete_self"), { status: 409 });
    usersState.users = usersState.users.filter((u) => u.id !== params.id);
    return new HttpResponse(null, { status: 204 });
  }),
  http.get(`${API}/projects/:id/shares`, ({ params }) => HttpResponse.json(usersState.shares[String(params.id)] ?? [])),
  http.put(`${API}/projects/:id/shares/:userId`, ({ params }) => {
    const user = usersState.users.find((u) => u.id === params.userId);
    if (!user) return HttpResponse.json(errorBody("user_not_found"), { status: 404 });
    const list = (usersState.shares[String(params.id)] ??= []);
    if (!list.some((s) => s.user_id === user.id)) list.push({ user_id: user.id, email: user.email, created_at: new Date().toISOString() });
    return new HttpResponse(null, { status: 204 });
  }),
  http.delete(`${API}/projects/:id/shares/:userId`, ({ params }) => {
    usersState.shares[String(params.id)] = (usersState.shares[String(params.id)] ?? []).filter((s) => s.user_id !== params.userId);
    return new HttpResponse(null, { status: 204 });
  }),
];
