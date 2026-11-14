import { http, HttpResponse } from "msw";
import { API } from "../api-base";
import { errorBody, mockId, registerReset } from "../mock-state";
import type { Project, ProjectSummary } from "@/types/projects/project.types";

// Synthetic coordinates: tests never carry a real preset location (BR-18).
export const SYNTHETIC = { lat: 10.12345, lon: -70.54321, elevation_m: 812, air_density_kg_m3: 1.129 };

export function makeProject(over: Partial<Project> = {}): Project {
  return {
    id: mockId("p"),
    name: "Edificio de la calle 5",
    lat: null,
    lon: null,
    elevation_m: null,
    elevation_source: null,
    air_density_kg_m3: null,
    analysis_height_m: 1.5,
    role_on_project: "owner",
    created_at: "2026-11-10T09:00:00Z",
    updated_at: "2026-11-13T10:00:00Z",
    ...over,
  };
}

export const projectsState = { projects: [] as Project[] };
registerReset(() => {
  projectsState.projects = [
    makeProject({ id: "00000000-0000-4000-8000-0000000000p1", ...SYNTHETIC, elevation_source: "open_meteo" }),
    makeProject({ id: "00000000-0000-4000-8000-0000000000p2", name: "Conjunto norte", updated_at: "2026-11-12T08:00:00Z" }),
  ];
});

function summary(p: Project): ProjectSummary {
  return { id: p.id, name: p.name, has_location: p.lat !== null, updated_at: p.updated_at ?? "", role_on_project: p.role_on_project };
}

function find(id: string | readonly string[] | undefined): Project | undefined {
  return projectsState.projects.find((p) => p.id === id);
}

const notFound = () => HttpResponse.json(errorBody("project_not_found"), { status: 404 });

export const projectsHandlers = [
  http.get(`${API}/projects`, () => HttpResponse.json(projectsState.projects.map(summary))),
  http.post(`${API}/projects`, async ({ request }) => {
    const { name } = (await request.json()) as { name: string };
    const project = makeProject({ name, updated_at: new Date().toISOString() });
    projectsState.projects.unshift(project);
    return HttpResponse.json(project, { status: 201 });
  }),
  http.get(`${API}/projects/:id`, ({ params }) => {
    const p = find(params.id);
    return p ? HttpResponse.json(p) : notFound();
  }),
  http.patch(`${API}/projects/:id`, async ({ params, request }) => {
    const p = find(params.id);
    if (!p) return notFound();
    Object.assign(p, (await request.json()) as Partial<Project>, { updated_at: new Date().toISOString() });
    return HttpResponse.json(p);
  }),
  http.delete(`${API}/projects/:id`, ({ params }) => {
    projectsState.projects = projectsState.projects.filter((p) => p.id !== params.id);
    return new HttpResponse(null, { status: 204 });
  }),
  http.post(`${API}/projects/:id/duplicate`, ({ params }) => {
    const p = find(params.id);
    if (!p) return notFound();
    const copy = { ...p, id: mockId("p"), name: `Copia de ${p.name}`, updated_at: new Date().toISOString() };
    projectsState.projects.unshift(copy);
    return HttpResponse.json(copy, { status: 201 });
  }),
];
