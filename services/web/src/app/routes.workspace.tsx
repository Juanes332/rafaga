import { createRoute, redirect } from "@tanstack/react-router";
import { projectQueryOptions } from "@/api/projects/projects.queries";
import { AlternativesStep } from "@/components/alternatives/AlternativesStep/AlternativesStep";
import { CompareScreen } from "@/components/compare/CompareScreen/CompareScreen";
import { GeometryStep } from "@/components/geometry/GeometryStep/GeometryStep";
import { LocationStep } from "@/components/location/LocationStep/LocationStep";
import { ReportsScreen } from "@/components/reports/ReportsScreen/ReportsScreen";
import { ResultsStep } from "@/components/results/ResultsStep/ResultsStep";
import { SimulateStep } from "@/components/simulations/SimulateStep/SimulateStep";
import { WindStep } from "@/components/wind/WindStep/WindStep";
import { WorkspaceShell } from "@/components/workspace/WorkspaceShell/WorkspaceShell";
import { queryClient } from "./query-client";
import { authedRoute } from "./routes.root";

export interface CompareSearch {
  a?: string;
  b?: string;
}

export const workspaceRoute = createRoute({
  getParentRoute: () => authedRoute,
  path: "/projects/$projectId",
  loader: ({ params }) => queryClient.ensureQueryData(projectQueryOptions(params.projectId)).catch(() => undefined),
  component: WorkspaceShell,
});

const parent = () => workspaceRoute;

export const workspaceIndexRoute = createRoute({
  getParentRoute: parent,
  path: "/",
  beforeLoad: ({ params }) => {
    throw redirect({ to: "/projects/$projectId/location", params: { projectId: params.projectId } });
  },
});
export const locationRoute = createRoute({ getParentRoute: parent, path: "location", component: LocationStep });
export const geometryRoute = createRoute({ getParentRoute: parent, path: "geometry", component: GeometryStep });
export const windRoute = createRoute({ getParentRoute: parent, path: "wind", component: WindStep });
export const alternativesRoute = createRoute({ getParentRoute: parent, path: "alternatives", component: AlternativesStep });
export const simulateRoute = createRoute({ getParentRoute: parent, path: "simulate", component: SimulateStep });
export const resultsRoute = createRoute({ getParentRoute: parent, path: "results/$resultId", component: ResultsStep });
export const reportsRoute = createRoute({ getParentRoute: parent, path: "reports", component: ReportsScreen });

/** Full-screen comparison lives outside the shell (no rail, no inspector). */
export const compareRoute = createRoute({
  getParentRoute: () => authedRoute,
  path: "/projects/$projectId/compare",
  validateSearch: (s: Record<string, unknown>): CompareSearch => ({
    a: typeof s.a === "string" ? s.a : undefined,
    b: typeof s.b === "string" ? s.b : undefined,
  }),
  component: CompareScreen,
});
